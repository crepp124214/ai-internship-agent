# tests/integration/test_agent_chat_sse.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


class TestAgentChatSSE:
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_agent_chat_returns_sse_content_type(self):
        """POST /agent/chat 返回 SSE 流"""
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
                    "/api/v1/agent/chat",
                    json={"task": "帮我定制简历", "context": {}},
                    headers=headers,
                )
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers.get("content-type", "")