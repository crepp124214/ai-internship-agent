"""
API集成测试（历史版本，已由更细粒度的 test_*_api.py 替代）
"""

import pytest

pytestmark = pytest.mark.skip(reason="legacy integration tests superseded by scoped api suites")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.data_access.database import Base, get_db
from src.presentation.schemas.user import UserCreate
from src.presentation.schemas.resume import ResumeCreate


# 创建测试数据库引擎
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    """测试数据库fixture"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """测试客户端fixture"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestHealthCheck:
    """测试健康检查接口"""

    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "AI实习求职Agent系统"
        assert "version" in response.json()
        assert "docs" in response.json()

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestUserAPI:
    """测试用户管理API"""

    def test_create_user(self, client):
        """测试创建用户"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "name": "测试用户",
            "phone": "13800138000",
            "bio": "这是一个测试用户"
        }
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data

    def test_get_user(self, client):
        """测试获取用户"""
        # 先创建用户
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "name": "测试用户"
        }
        create_response = client.post("/api/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        # 获取用户
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "testuser"

    def test_get_user_not_found(self, client):
        """测试获取不存在的用户"""
        response = client.get("/api/v1/users/999")
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    def test_update_user(self, client):
        """测试更新用户"""
        # 先创建用户
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "name": "测试用户"
        }
        create_response = client.post("/api/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        # 更新用户
        update_data = {
            "name": "更新后的用户",
            "bio": "更新后的简介"
        }
        response = client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的用户"
        assert data["bio"] == "更新后的简介"

    def test_update_user_not_found(self, client):
        """测试更新不存在的用户"""
        update_data = {"name": "更新后的用户"}
        response = client.put("/api/v1/users/999", json=update_data)
        assert response.status_code == 404

    def test_delete_user(self, client):
        """测试删除用户"""
        # 先创建用户
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "name": "测试用户"
        }
        create_response = client.post("/api/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        # 删除用户
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 204

        # 验证用户已删除
        get_response = client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client):
        """测试删除不存在的用户"""
        response = client.delete("/api/v1/users/999")
        assert response.status_code == 404

    def test_list_users(self, client):
        """测试获取用户列表"""
        # 创建多个用户
        for i in range(3):
            user_data = {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "password123",
                "name": f"用户{i}"
            }
            client.post("/api/v1/users/", json=user_data)

        # 获取用户列表
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_login_not_implemented(self, client):
        """测试登录接口（未实现）"""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        response = client.post("/api/v1/users/login/", json=login_data)
        assert response.status_code == 501


class TestResumeAPI:
    """测试简历管理API"""

    def test_create_resume(self, client):
        """测试创建简历"""
        resume_data = {
            "title": "我的简历",
            "file_path": "/path/to/resume.pdf"
        }
        response = client.post("/api/v1/resumes/", json=resume_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "我的简历"
        assert "id" in data

    def test_get_resume(self, client):
        """测试获取简历"""
        # 先创建简历
        resume_data = {
            "title": "我的简历",
            "file_path": "/path/to/resume.pdf"
        }
        create_response = client.post("/api/v1/resumes/", json=resume_data)
        resume_id = create_response.json()["id"]

        # 获取简历
        response = client.get(f"/api/v1/resumes/{resume_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resume_id
        assert data["title"] == "我的简历"

    def test_get_resume_not_found(self, client):
        """测试获取不存在的简历"""
        response = client.get("/api/v1/resumes/999")
        assert response.status_code == 404

    def test_update_resume(self, client):
        """测试更新简历"""
        # 先创建简历
        resume_data = {
            "title": "我的简历",
            "file_path": "/path/to/resume.pdf"
        }
        create_response = client.post("/api/v1/resumes/", json=resume_data)
        resume_id = create_response.json()["id"]

        # 更新简历
        update_data = {
            "title": "更新后的简历",
            "processed_content": "处理后的内容"
        }
        response = client.put(f"/api/v1/resumes/{resume_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的简历"

    def test_delete_resume(self, client):
        """测试删除简历"""
        # 先创建简历
        resume_data = {
            "title": "我的简历",
            "file_path": "/path/to/resume.pdf"
        }
        create_response = client.post("/api/v1/resumes/", json=resume_data)
        resume_id = create_response.json()["id"]

        # 删除简历
        response = client.delete(f"/api/v1/resumes/{resume_id}")
        assert response.status_code == 204

        # 验证简历已删除
        get_response = client.get(f"/api/v1/resumes/{resume_id}")
        assert get_response.status_code == 404

    def test_list_resumes(self, client):
        """测试获取简历列表"""
        # 创建多个简历
        for i in range(3):
            resume_data = {
                "title": f"简历{i}",
                "file_path": f"/path/to/resume{i}.pdf"
            }
            client.post("/api/v1/resumes/", json=resume_data)

        # 获取简历列表
        response = client.get("/api/v1/resumes/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
