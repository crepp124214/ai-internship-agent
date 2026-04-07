"""
端到端集成测试：验证完整的 ReAct 循环
使用 mock LLM，验证状态流转和工具调用
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.tool_registry import ToolRegistry
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.tools.base_tool import BaseTool


class EchoTool(BaseTool):
    """Echo tool for testing"""
    name: str = "echo"
    description: str = "Echoes back the input"

    def _execute_sync(self, tool_input: dict, runtime=None, context=None) -> dict:
        return {"echoed": tool_input.get("message", "")}


@pytest.fixture
def memory_store():
    redis_mock = MagicMock()
    redis_mock.rpush = MagicMock()
    redis_mock.expire = MagicMock()
    redis_mock.lrange = MagicMock(return_value=[])
    redis_mock.delete = MagicMock()

    chroma_mock = MagicMock()
    return MemoryStore(redis_client=redis_mock, chroma_client=chroma_mock)


@pytest.fixture
def tool_registry():
    registry = ToolRegistry()
    registry.register(EchoTool())
    return registry


@pytest.mark.asyncio
async def test_react_loop_with_tool_call(memory_store, tool_registry):
    """验证 ReAct 循环中工具调用的完整流程"""
    # 状态机
    sm = StateMachine()

    # Mock LLM：第一次返回 tool_call，第二次返回文本
    call_count = 0
    async def mock_chat(messages, tools=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # LLM 选择调用工具
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "echo",
                        "arguments": '{"message": "hello world"}',
                    },
                }],
            }
        else:
            return {"role": "assistant", "content": "Tool returned: hello world"}

    mock_llm = MagicMock(spec=LiteLLMAdapter)
    mock_llm.chat = mock_chat

    # Context builder
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.build_sync = MagicMock(return_value=[
        {"role": "system", "content": "You are a test agent."}
    ])

    executor = AgentExecutor(
        llm=mock_llm,
        tools=tool_registry,
        memory=memory_store,
        state_machine=sm,
        context_builder=context_builder,
    )

    results = []
    async for chunk in executor.execute("test task", "session-1"):
        results.append(chunk)

    # 验证最终状态
    assert sm.get_state() == "done"
    # 验证 LLM 被调用了 2 次（tool → text）
    assert call_count == 2
    # 验证返回了工具结果
    assert any("hello world" in r for r in results)


@pytest.mark.asyncio
async def test_react_loop_text_only(memory_store, tool_registry):
    """验证纯文本响应（无工具调用）的 ReAct 循环"""
    sm = StateMachine()

    mock_llm = MagicMock(spec=LiteLLMAdapter)
    mock_llm.chat = AsyncMock(return_value={
        "role": "assistant",
        "content": "This is a direct answer.",
    })

    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.build_sync = MagicMock(return_value=[
        {"role": "system", "content": "You are a test agent."}
    ])

    executor = AgentExecutor(
        llm=mock_llm,
        tools=tool_registry,
        memory=memory_store,
        state_machine=sm,
        context_builder=context_builder,
    )

    results = []
    async for chunk in executor.execute("what is 2+2", "session-2"):
        results.append(chunk)

    assert "".join(results) == "This is a direct answer."
    assert sm.get_state() == "done"
    assert mock_llm.chat.call_count == 1
