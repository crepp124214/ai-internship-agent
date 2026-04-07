# tests/e2e/conftest.py
"""Playwright E2E 测试配置"""
import os
import time
import pytest
from playwright.sync_api import sync_playwright, Browser, Page


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


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