# tests/e2e/conftest.py
"""Playwright E2E 测试配置"""
import os
import time
import pytest
from playwright.sync_api import sync_playwright, Browser, Page


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def browser():
    """启动浏览器"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def page(browser: Browser):
    """打开新页面"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def api_client():
    """API 测试客户端"""
    import httpx
    client = httpx.Client(base_url=API_BASE_URL, timeout=30)
    yield client
    client.close()


@pytest.fixture
def wait_for_api():
    """等待 API 就绪"""
    import httpx
    client = httpx.Client(base_url=API_BASE_URL, timeout=10)
    max_retries = 30
    for i in range(max_retries):
        try:
            response = client.get("/docs")
            if response.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        pytest.fail("API did not become ready in time")
    client.close()
    yield


@pytest.fixture
def auth_header(wait_for_api):
    """创建测试用户并返回 Bearer 认证头"""
    import uuid
    import httpx

    client = httpx.Client(base_url=API_BASE_URL, timeout=30)

    # 创建唯一用户名
    username = f"gp_user_{uuid.uuid4().hex[:12]}"
    password = "TestPassword123!"

    # 1. 创建用户（POST /api/v1/users/ 无需认证）
    user_resp = client.post(
        "/api/v1/users/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "name": username,
        },
    )
    # 用户可能已存在（ idempotent），只要不是 500 即可
    assert user_resp.status_code in (200, 201), f"User creation failed: {user_resp.text}"

    # 2. 登录获取 access token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    access_token = login_resp.json()["access_token"]

    client.close()
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def golden_path_api_client(auth_header):
    """返回携带认证头的 httpx.Client，用于黄金路径 API 测试"""
    import httpx
    client = httpx.Client(
        base_url=API_BASE_URL,
        timeout=30,
        headers=auth_header,
    )
    yield client
    client.close()
