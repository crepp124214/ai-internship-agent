import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.infrastructure.database.session import Base, get_db
from backend.main import app
# 仅当环境变量明确开启时才运行
ENABLE_REAL_LLM = os.getenv("ENABLE_REAL_LLM", "").lower() == "true"
HAS_API_KEY = bool(os.getenv("MINIMAX_API_KEY", "").strip())
skip_if_no_real_llm = pytest.mark.skipif(
    not (ENABLE_REAL_LLM and HAS_API_KEY),
    reason="ENABLE_REAL_LLM=true 且 MINIMAX_API_KEY 必须设置才能运行",
)
TEST_DB = "sqlite://"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
def _create_test_user_and_resume(client):
    """准备最小测试数据：用户 + 简历"""
    # 1. 注册用户
    client.post("/api/v1/users/", json={
        "username": "minimaxtest",
        "email": "minimax@test.com",
        "name": "MiniMax Test",
        "password": "test123"
    })
    
    # 2. 登录获取 Token
    login = client.post("/api/v1/auth/login", json={
        "username": "minimaxtest",
        "password": "test123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # 3. 创建简历
    resume = client.post("/api/v1/resumes/", json={
        "title": "MiniMax Test Resume",
        "file_path": "/tmp/test.pdf"
    }, headers=headers)
    resume_id = resume.json()["id"]
    
    # 4. 注入测试文本（确保 AI 有内容可分析）
    client.put(f"/api/v1/resumes/{resume_id}", json={
        "resume_text": "Senior Python developer with 3 years experience in FastAPI, PostgreSQL, and cloud architecture. Led team of 5 engineers."
    }, headers=headers)
    return resume_id, headers
@skip_if_no_real_llm
class TestMiniMaxSmoke:
    """MiniMax 真实 API 端到端冒烟测试"""
    def test_resume_summary_with_minimax(self, client):
        """测试简历摘要功能"""
        resume_id, headers = _create_test_user_and_resume(client)
        
        # 调用真实 AI 接口（不 mock）
        resp = client.post(
            f"/api/v1/resumes/{resume_id}/summary/",
            json={"target_role": "Backend Engineer"},
            headers=headers,
        )
        assert resp.status_code == 200, f"请求失败: {resp.text}"
        data = resp.json()
        
        # 验证结构，不验证具体内容（LLM 输出非确定性）
        assert data["mode"] == "summary"
        assert data["resume_id"] == resume_id
        assert len(data["content"]) > 20, "返回内容过短，可能未走真实 API"
        assert data["provider"] in ("minimax", "mock"), f"未知 provider: {data['provider']}"
        print(f"\n✅ MiniMax 简历摘要返回: {data['content'][:100]}...")
    def test_job_match_with_minimax(self, client):
        """测试岗位匹配功能"""
        _, headers = _create_test_user_and_resume(client)
        
        # 创建岗位
        job = client.post("/api/v1/jobs/", json={
            "title": "Python Intern",
            "company": "TestCo",
            "location": "Remote",
            "description": "Looking for Python developer with FastAPI experience.",
            "requirements": "Python, FastAPI",
            "source": "internal",
            "salary": "10k",
            "work_type": "internship",
            "experience": "0-1",
            "education": "Bachelor",
            "welfare": "Remote",
            "tags": "python"
        }, headers=headers)
        job_id = job.json()["id"]
        resume_id = client.get("/api/v1/resumes/", headers=headers).json()[0]["id"]
        resp = client.post(
            f"/api/v1/jobs/{job_id}/match/",
            json={"resume_id": resume_id},
            headers=headers,
        )
        assert resp.status_code == 200, f"请求失败: {resp.text}"
        data = resp.json()
        assert data["mode"] == "job_match"
        assert isinstance(data["score"], int), f"score 应为整数: {type(data['score'])}"
        print(f"\n✅ MiniMax 岗位匹配得分: {data['score']}/100")
        print(f"   反馈: {data['feedback'][:100]}...")
    def test_interview_questions_with_minimax(self, client):
        """测试面试题目生成功能"""
        _, headers = _create_test_user_and_resume(client)
        
        resp = client.post(
            "/api/v1/interview/questions/generate/",
            json={
                "job_context": "Python Backend Developer position requiring FastAPI, PostgreSQL, and system design skills.",
                "count": 3  # 限制题目数量控制成本
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"请求失败: {resp.text}"
        data = resp.json()
        assert data["mode"] == "question_generation"
        assert len(data["questions"]) == 3, f"应返回 3 道题，实际 {len(data['questions'])}"
        print(f"\n✅ MiniMax 生成 {len(data['questions'])} 道面试题:")
        for i, q in enumerate(data["questions"], 1):
            print(f"   {i}. {q['question_text'][:80]}...")