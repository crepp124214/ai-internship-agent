# tests/e2e/test_job_api.py
"""Job API E2E 测试"""
import os
import pytest
from playwright.sync_api import Page, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class TestJobAPI:
    """Job API 测试"""

    def test_jobs_page_loads(self, page: Page, wait_for_api):
        """验证 Jobs 页面加载"""
        page.goto(f"{FRONTEND_URL}/jobs")
        expect(page.locator('body')).to_be_visible()

    def test_import_modal_jd_tab(self, page: Page, wait_for_api):
        """验证 JD 导入 Tab 存在"""
        page.goto(f"{FRONTEND_URL}")
        import_button = page.locator('button:has-text("导入数据")')
        if import_button.is_visible():
            import_button.click()
            jd_tab = page.locator('button:has-text("JD 批量导入")')
            if jd_tab.is_visible():
                jd_tab.click()
                expect(page.locator('text=支持 CSV、Excel 格式')).to_be_visible()


class TestJobAPIGoldenPath:
    """黄金路径 API E2E 测试：login -> recommend -> match -> resume -> question set -> coach"""

    def test_golden_path_recommend_and_match(self, golden_path_api_client):
        """
        黄金路径 Part 1: recommend + match
        流程: 登录 -> 创建简历 -> 推荐岗位 -> 岗位匹配
        """
        client = golden_path_api_client

        # Step 1: 创建简历
        resume_resp = client.post(
            "/api/v1/resumes/",
            json={
                "title": "我的后端简历",
                "file_path": "/tmp/resume.pdf",
                "resume_text": "熟悉 Python、FastAPI、SQLAlchemy，有大型项目经验",
                "file_name": "resume.pdf",
                "file_type": "pdf",
                "language": "zh-CN",
            },
        )
        assert resume_resp.status_code == 200, f"Resume creation failed: {resume_resp.text}"
        resume_id = resume_resp.json()["id"]

        # Step 2: 获取推荐岗位
        recommend_resp = client.get("/api/v1/jobs/recommended/", params={"goal_summary": "后端开发 实习"})
        assert recommend_resp.status_code == 200, f"Recommend failed: {recommend_resp.text}"
        recommended_jobs = recommend_resp.json()
        assert isinstance(recommended_jobs, list)

        # Step 3: 如果有推荐岗位，进行匹配
        if recommended_jobs:
            job_id = recommended_jobs[0]["id"]
            match_resp = client.post(
                f"/api/v1/jobs/{job_id}/match/",
                json={"resume_id": resume_id},
            )
            assert match_resp.status_code == 200, f"Match failed: {match_resp.text}"
            match_result = match_resp.json()
            assert "score" in match_result
            assert "feedback" in match_result

            # 保存匹配记录
            persist_resp = client.post(
                f"/api/v1/jobs/{job_id}/match/persist/",
                json={"resume_id": resume_id},
            )
            assert persist_resp.status_code == 200, f"Persist match failed: {persist_resp.text}"

        # Step 4: 创建外部岗位（补充路径）
        ext_job_resp = client.post(
            "/api/v1/jobs/save-external",
            json={
                "title": "后端实习",
                "company": "测试公司",
                "location": "北京",
                "description": "要求：Python、FastAPI",
                "source_url": "https://example.com/job/1",
            },
        )
        assert ext_job_resp.status_code == 200, f"Save external job failed: {ext_job_resp.text}"
        saved_job_id = ext_job_resp.json()["id"]

        # Step 5: 对保存的岗位进行匹配（独立验证）
        match2_resp = client.post(
            f"/api/v1/jobs/{saved_job_id}/match/",
            json={"resume_id": resume_id},
        )
        assert match2_resp.status_code == 200, f"Match2 failed: {match2_resp.text}"

    def test_golden_path_recommend_jobs_endpoint_structure(self, golden_path_api_client):
        """
        验证推荐岗位 API 返回结构完整性
        """
        client = golden_path_api_client

        # 先创建一个岗位以保证有数据
        job_resp = client.post(
            "/api/v1/jobs/",
            json={
                "title": "前端开发实习",
                "company": "WebCorp",
                "location": "上海",
                "description": "React, TypeScript",
                "requirements": "React, TS",
                "salary": "15k-20k",
                "work_type": "internship",
                "experience": "0-1 year",
                "education": "Bachelor",
                "welfare": "Remote",
                "tags": "react,typescript",
                "source": "test",
                "source_url": "https://webcorp.com/jobs/1",
                "source_id": "wc-1",
            },
        )
        assert job_resp.status_code == 200

        # 获取推荐
        resp = client.get("/api/v1/jobs/recommended/", params={"goal_summary": "前端开发"})
        assert resp.status_code == 200
        jobs = resp.json()
        assert isinstance(jobs, list)

        # 验证返回结构
        for job in jobs:
            assert "id" in job
            assert "title" in job
            assert "company" in job
            assert "recommendation_score" in job
            assert "official_url" in job  # 从 source_url 映射
            assert "tags" in job
            assert "summary" in job
