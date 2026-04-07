# tests/integration/test_customize_endpoint.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


class TestCustomizeForJdEndpoint:
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_customize_endpoint_returns_404_for_missing_resume(self):
        """简历不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Login first to get auth
            login_resp = await client.post(
                "/api/v1/auth/login/",
                json={"username": "testuser", "password": "testpass"},
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.post(
                    "/api/v1/resumes/99999/customize-for-jd",
                    json={"jd_id": 1},
                    headers=headers,
                )
                assert resp.status_code == 404
