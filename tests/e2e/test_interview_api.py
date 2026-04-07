# tests/e2e/test_interview_api.py
"""Interview API E2E 测试"""
import os
import pytest
from playwright.sync_api import Page, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class TestInterviewAPI:
    """Interview API 测试"""

    def test_interview_page_loads(self, page: Page, wait_for_api):
        """验证 Interview 页面加载"""
        page.goto(f"{FRONTEND_URL}/interview")
        expect(page.locator('body')).to_be_visible()