"""
pytest配置文件
定义测试fixture和配置
"""

import os

# 设置测试环境变量以绕过安全检查
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-12345")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.infrastructure.database.session import Base, get_db
from backend.app.schemas.user import UserCreate
from backend.app.schemas.resume import ResumeCreate
from backend.app.schemas.job import JobCreate


@pytest.fixture
def sample_config():
    """示例配置fixture"""
    return {
        "app_name": "Test Agent",
        "debug": True,
    }


@pytest.fixture
def sample_resume_text():
    """示例简历文本fixture"""
    return """
    张三
    软件工程师实习生

    教育背景
    清华大学 - 计算机科学与技术 - 本科
    2020.09 - 2024.06

    技能
    Python, Java, SQL, FastAPI, React
    """


@pytest.fixture
def sample_user_data():
    """示例用户数据fixture"""
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
        name="测试用户",
        phone="13800138000",
        bio="这是一个测试用户"
    )


@pytest.fixture
def sample_resume_data():
    """示例简历数据fixture"""
    return ResumeCreate(
        title="我的简历",
        file_path="/tmp/test_resume.pdf"
    )


@pytest.fixture
def test_db():
    """测试数据库fixture"""
    # 使用内存SQLite数据库进行测试
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def llm_config():
    """LLM配置fixture"""
    return {
        "api_key": "test_key",
        "model": "gpt-4",
        "temperature": 0.7,
    }


@pytest.fixture
def agent_config():
    """Agent配置fixture"""
    return {
        "name": "test_agent",
        "description": "Test Agent",
    }


# ==================== FastAPI测试客户端fixture ====================

@pytest.fixture
def test_engine():
    """测试数据库引擎fixture"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def test_db_session(test_engine):
    """测试数据库会话fixture"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client(test_db_session):
    """FastAPI测试客户端fixture"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ==================== 业务数据fixture ====================

@pytest.fixture
def sample_job_data():
    """示例岗位数据fixture"""
    return {
        "title": "软件工程师实习生",
        "company": "测试科技公司",
        "location": "北京",
        "salary": "10k-15k",
        "description": "负责软件开发和测试工作",
        "requirements": "Python, FastAPI, SQL",
        "benefits": "五险一金, 周末双休",
        "job_url": "https://example.com/job/123",
        "source": "test_source"
    }


@pytest.fixture
def sample_interview_data():
    """示例面试数据fixture"""
    return {
        "job_id": 1,
        "question_id": 1,
        "user_answer": "这是我的回答",
        "ai_evaluation": "回答很详细",
        "score": 85,
        "feedback": "建议补充更多实践案例"
    }


@pytest.fixture
def sample_tracker_data():
    """示例追踪数据fixture"""
    return {
        "job_id": 1,
        "resume_id": 1,
        "status": "applied",
        "notes": "已投递简历"
    }


# ==================== 异步测试支持 ====================

@pytest.fixture
def event_loop():
    """创建事件循环用于异步测试"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== 认证fixture ====================

@pytest.fixture
def auth_headers():
    """测试认证头fixture"""
    return {"Authorization": "Bearer valid_token"}


@pytest.fixture
def test_user_in_db(test_db_session):
    """在测试数据库中创建测试用户"""
    from src.data_access.repositories.user_repository import user_repository

    user = user_repository.create(test_db_session, {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "name": "测试用户",
        "phone": "13800138000",
        "bio": "测试用户简介"
    })
    test_db_session.commit()
    test_db_session.refresh(user)
    return user
