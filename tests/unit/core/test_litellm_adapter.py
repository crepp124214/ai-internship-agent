import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.llm.litellm_adapter import LiteLLMAdapter

@pytest.fixture
def adapter():
    return LiteLLMAdapter(model="gpt-4o-mini", api_key="test-key")

def test_adapter_stores_model_and_key(adapter):
    assert adapter.model == "gpt-4o-mini"
    assert adapter.api_key == "test-key"

@pytest.mark.asyncio
async def test_chat_returns_content():
    adapter = LiteLLMAdapter(model="gpt-4o-mini", api_key="test-key")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="hello"))]

    with patch("src.core.llm.litellm_adapter.acompletion", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await adapter.chat(messages=[{"role": "user", "content": "hi"}])
        assert result["content"] == "hello"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["messages"] == [{"role": "user", "content": "hi"}]

@pytest.mark.asyncio
async def test_chat_with_tools_includes_tools_param():
    adapter = LiteLLMAdapter(model="gpt-4o-mini", api_key="test-key")
    tools = [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="It is sunny"))]

    with patch("src.core.llm.litellm_adapter.acompletion", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        await adapter.chat(messages=[{"role": "user", "content": "weather"}], tools=tools)
        call_kwargs = mock_create.call_args.kwargs
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == tools