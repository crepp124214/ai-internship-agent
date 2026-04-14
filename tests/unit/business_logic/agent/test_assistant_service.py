import pytest
from src.business_logic.agent.assistant_service import AssistantService, AssistantContext
from unittest.mock import AsyncMock, MagicMock, patch

def test_build_system_prompt_for_resume_page():
    service = AssistantService()
    prompt = service.build_system_prompt(page="resume", resource_id=123)
    assert "简历" in prompt
    assert "123" in prompt

def test_build_system_prompt_for_job_page():
    service = AssistantService()
    prompt = service.build_system_prompt(page="job", resource_id=456)
    assert "岗位" in prompt
    assert "456" in prompt

def test_build_context_creates_valid_context():
    service = AssistantService()
    ctx = service.build_context(
        page="resume",
        resource_id=1,
        resource_ids=[1, 2],
        history=[{"role": "user", "content": "hello"}]
    )
    assert ctx["page"] == "resume"
    assert ctx["resource_id"] == 1
    assert len(ctx["history"]) == 1


def test_build_llm_for_job_context_uses_saved_user_config():
    service = AssistantService()
    mock_db = object()
    saved_config = {
        "provider": "zhipu",
        "model": "glm-4.7",
        "api_key": "secret",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "temperature": 0.7,
    }

    with patch(
        "src.business_logic.agent.assistant_service.user_llm_config_service.get_config_for_agent",
        return_value=saved_config,
    ):
        llm = service._build_llm_for_context(db=mock_db, user_id=1, page="job")

    assert llm.provider == "zhipu"
    assert llm.model == "glm-4.7"
    assert llm.api_key == "secret"


@pytest.mark.asyncio
async def test_chat_uses_direct_generation_for_non_openai_provider():
    service = AssistantService()
    mock_db = object()
    llm = MagicMock()
    llm.provider = "zhipu"
    llm.generate = AsyncMock(return_value="基于真实岗位和简历上下文的建议")

    with patch.object(service, "_build_llm_for_context", return_value=llm), patch.object(
        service, "_build_resource_context", return_value="当前岗位上下文：后端开发实习\n当前简历上下文：Python 项目经历"
    ):
        events = []
        async for event in service.chat(
            "这个岗位和我的简历匹配吗？",
            AssistantContext(page="job", resource_id=1, resource_ids=[21]),
            db=mock_db,
            user_id=28,
        ):
            events.append(event)

    llm.generate.assert_awaited_once()
    assert events[0]["type"] == "step"
    assert "真实岗位和简历上下文" in events[0]["content"]
    assert events[-1]["type"] == "done"
