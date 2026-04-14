# tests/e2e/test_interview_api.py
"""Interview API E2E 测试"""
import os
import pytest
from playwright.sync_api import Page, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class TestInterviewAPI:
    """Interview API 测试"""

    def test_interview_page_loads(self, page: Page, wait_for_api):
        """验证 Interview 页面加载"""
        page.goto(f"{FRONTEND_URL}/interview")
        expect(page.locator('body')).to_be_visible()


class TestInterviewAPIGoldenPath:
    """黄金路径 API E2E 测试：question set -> coach"""

    def test_golden_path_resume_customize_and_question_set_to_coach(self, golden_path_api_client):
        """
        黄金路径 Part 2: resume customize -> question set -> coach
        完整流程: 创建简历 -> 创建岗位 -> 简历定制 JD -> 创建题集 -> 从题集启动教练
        """
        client = golden_path_api_client

        # Step 1: 创建简历
        resume_resp = client.post(
            "/api/v1/resumes/",
            json={
                "title": "我的简历",
                "file_path": "/tmp/resume.pdf",
                "resume_text": "熟悉 Python、FastAPI、PostgreSQL，有后端开发经验",
                "file_name": "resume.pdf",
                "file_type": "pdf",
                "language": "zh-CN",
            },
        )
        assert resume_resp.status_code == 200, f"Resume creation failed: {resume_resp.text}"
        resume_id = resume_resp.json()["id"]

        # Step 2: 创建岗位 JD
        job_resp = client.post(
            "/api/v1/jobs/",
            json={
                "title": "后端开发实习",
                "company": "AI Corp",
                "location": "北京",
                "description": "要求：Python、FastAPI、SQLAlchemy、PostgreSQL，有大型项目经验",
                "requirements": "Python, FastAPI, PostgreSQL",
                "salary": "15k-25k",
                "work_type": "internship",
                "experience": "0-1 year",
                "education": "Bachelor",
                "welfare": "Remote",
                "tags": "python,fastapi,postgresql",
                "source": "test",
                "source_url": "https://aicorp.com/jobs/backend",
                "source_id": "ai-1",
            },
        )
        assert job_resp.status_code == 200, f"Job creation failed: {job_resp.text}"
        job_id = job_resp.json()["id"]

        # Step 3: 简历定制 JD（customize-for-jd）
        customize_resp = client.post(
            f"/api/v1/resumes/{resume_id}/customize-for-jd",
            json={
                "jd_id": job_id,
                "enable_match_report": True,
                "custom_instructions": "突出 Python 和 FastAPI 经验",
            },
        )
        assert customize_resp.status_code == 200, f"Customize failed: {customize_resp.text}"
        customize_result = customize_resp.json()
        assert "customized_resume" in customize_result
        assert "match_report" in customize_result

        # Step 4: 创建题集（包含生成的面试题）
        question_set_resp = client.post(
            "/api/v1/interview/question-sets",
            json={
                "title": "后端开发面试题集",
                "job_id": job_id,
                "resume_id": resume_id,
                "questions": [
                    {
                        "question_number": 1,
                        "question_text": "请介绍你使用 FastAPI 开发项目的经验",
                        "question_type": "technical",
                        "difficulty": "medium",
                        "category": "backend",
                    },
                    {
                        "question_number": 2,
                        "question_text": "如何排查 FastAPI 应用的超时问题？",
                        "question_type": "technical",
                        "difficulty": "medium",
                        "category": "backend",
                    },
                ],
            },
        )
        assert question_set_resp.status_code == 201, f"Question set creation failed: {question_set_resp.text}"
        question_set = question_set_resp.json()
        assert question_set["title"] == "后端开发面试题集"
        assert len(question_set["questions"]) == 2
        question_set_id = question_set["id"]

        # Step 5: 获取题集列表
        list_resp = client.get("/api/v1/interview/question-sets")
        assert list_resp.status_code == 200, f"List question sets failed: {list_resp.text}"
        question_sets = list_resp.json()
        assert len(question_sets) >= 1
        assert any(qs["id"] == question_set_id for qs in question_sets)

        # Step 6: 从题集启动教练
        coach_resp = client.post(f"/api/v1/interview/question-sets/{question_set_id}/start-coach")
        assert coach_resp.status_code == 200, f"Start coach from question set failed: {coach_resp.text}"
        coach_result = coach_resp.json()
        assert "session_id" in coach_result
        assert "opening_message" in coach_result
        assert "first_question" in coach_result

    def test_golden_path_question_set_full_lifecycle(self, golden_path_api_client):
        """
        题集完整生命周期：创建 -> 更新 -> 获取单个 -> 列出全部
        """
        client = golden_path_api_client

        # 创建简历和岗位
        resume_resp = client.post(
            "/api/v1/resumes/",
            json={
                "title": "测试简历",
                "file_path": "/tmp/resume.pdf",
                "resume_text": "熟悉 Python",
                "file_name": "resume.pdf",
                "file_type": "pdf",
                "language": "zh-CN",
            },
        )
        assert resume_resp.status_code == 200
        resume_id = resume_resp.json()["id"]

        job_resp = client.post(
            "/api/v1/jobs/",
            json={
                "title": "Python 实习",
                "company": "PyCorp",
                "location": "远程",
                "description": "Python 开发",
                "requirements": "Python",
                "source": "test",
                "source_url": "https://pycorp.com/jobs/1",
                "source_id": "py-1",
            },
        )
        assert job_resp.status_code == 200
        job_id = job_resp.json()["id"]

        # 创建题集
        create_resp = client.post(
            "/api/v1/interview/question-sets",
            json={
                "title": "Python 面试题集",
                "job_id": job_id,
                "resume_id": resume_id,
                "questions": [
                    {
                        "question_number": 1,
                        "question_text": "什么是 Python GIL？",
                        "question_type": "technical",
                        "difficulty": "easy",
                        "category": "python",
                    },
                ],
            },
        )
        assert create_resp.status_code == 201
        qs_id = create_resp.json()["id"]

        # 获取单个题集
        get_resp = client.get(f"/api/v1/interview/question-sets/{qs_id}")
        assert get_resp.status_code == 200
        qs = get_resp.json()
        assert qs["id"] == qs_id
        assert qs["questions"][0]["question_text"] == "什么是 Python GIL？"

        # 更新题集
        update_resp = client.patch(
            f"/api/v1/interview/question-sets/{qs_id}",
            json={
                "title": "Python 面试题集（更新）",
                "status": "active",
            },
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Python 面试题集（更新）"

        # 列出全部题集
        list_resp = client.get("/api/v1/interview/question-sets")
        assert list_resp.status_code == 200
        all_qs = list_resp.json()
        assert any(q["id"] == qs_id for q in all_qs)
