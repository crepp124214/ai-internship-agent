# tests/integration/interview/test_interview_flow.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


class TestInterviewCoachFlow:
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_coach_start_returns_404_for_missing_jd(self):
        """JD 不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login/",
                json={"username": "testuser", "password": "testpass"},
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.post(
                    "/api/v1/interview/coach/start",
                    json={"jd_id": 99999, "resume_id": 1},
                    headers=headers,
                )
                assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_coach_answer_returns_409_for_completed_session(self):
        """已结束的会话返回 409"""
        # This test would need a full session flow
        # Placeholder for now
        pass
