# tests/e2e/test_agent_api.py
"""Agent API E2E 测试"""
import os
import re
import pytest
from playwright.sync_api import Page, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class TestAgentAPI:
    """Agent API 测试"""

    def test_dashboard_loads(self, page: Page, wait_for_api):
        """验证 Dashboard 加载"""
        page.goto(f"{FRONTEND_URL}")
        expect(page.locator('body')).to_be_visible()

    def test_api_docs_accessible(self, page: Page, wait_for_api):
        """验证 API 文档可访问"""
        page.goto(f"{API_BASE_URL}/docs")
        expect(page).to_have_title(re.compile("Swagger UI"))
