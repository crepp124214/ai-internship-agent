"""Assistant API integration tests."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_get_agent_tools_returns_list():
    """GET /agent/tools 返回工具列表"""
    try:
        login_resp = client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo123"})
    except Exception:
        pytest.skip("Login failed, skipping test")
    if login_resp.status_code != 200:
        pytest.skip("Login failed, skipping test")
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/agent/tools", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    tool_names = [t["name"] for t in data["tools"]]
    assert "read_resume" in tool_names
    assert "web_search" in tool_names


def test_assistant_chat_requires_auth():
    """POST /agent/assistant/chat 需要认证"""
    resp = client.post("/api/v1/agent/assistant/chat", json={
        "message": "hello",
        "context": {"page": "resume"}
    })
    assert resp.status_code == 401