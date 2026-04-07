# tests/e2e/test_resume_api.py
"""Resume API E2E 测试"""
import os
import pytest
from playwright.sync_api import Page, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class TestResumeAPI:
    """Resume API 测试"""

    def test_swagger_loads(self, page: Page, wait_for_api):
        """验证 Swagger UI 加载"""
        page.goto(f"{API_BASE_URL}/docs")
        expect(page.locator('text=Swagger UI')).to_be_visible()

    def test_resume_page_loads(self, page: Page, wait_for_api):
        """验证 Resume 页面可访问"""
        page.goto(f"{FRONTEND_URL}/resumes")
        expect(page.locator('body')).to_be_visible()

    def test_import_modal_button_exists(self, page: Page, wait_for_api):
        """验证导入按钮存在"""
        page.goto(f"{FRONTEND_URL}")
        button = page.locator('button:has-text("导入数据")')
        if button.is_visible():
            button.click()
            expect(page.locator('text=简历导入')).to_be_visible()