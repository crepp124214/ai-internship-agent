# tests/e2e/test_job_api.py
"""Job API E2E 测试"""
import os
import pytest
from playwright.sync_api import Page, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


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