import pytest
from unittest.mock import MagicMock, AsyncMock
from pydantic import BaseModel

from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.memory_store import MemoryStore, Turn
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.tool_registry import ToolRegistry
from src.core.tools.base_tool import BaseTool


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value={"role": "assistant", "content": "Hello, how can I help?"})
    return llm


@pytest.fixture
def mock_memory():
    memory = MagicMock(spec=MemoryStore)
    memory.get_turns = MagicMock(return_value=[])
    memory.add_turn = MagicMock()
    return memory


@pytest.fixture
def mock_context_builder():
    builder = MagicMock(spec=ContextBuilder)
    builder.build_sync = MagicMock(return_value=[
        {"role": "system", "content": "You are a helpful assistant."}
    ])
    return builder


@pytest.fixture
def executor(mock_llm, mock_memory, mock_context_builder):
    sm = StateMachine()
    registry = ToolRegistry()
    return AgentExecutor(
        llm=mock_llm,
        tools=registry,
        memory=mock_memory,
        state_machine=sm,
        context_builder=mock_context_builder,
    )


def test_executor_initial_state(executor):
    assert executor._state_machine.get_state() == "idle"


def test_executor_stores_dependencies(executor, mock_llm, mock_memory, mock_context_builder):
    assert executor._llm is mock_llm
    assert executor._memory is mock_memory
    assert executor._context_builder is mock_context_builder


@pytest.mark.asyncio
async def test_execute_yields_text_response(executor, mock_llm, mock_context_builder):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Done!"}
    results = []
    async for chunk in executor.execute("Hello", "session-1"):
        results.append(chunk)
    assert "".join(results) == "Done!"
    assert executor._state_machine.get_state() == "done"


@pytest.mark.asyncio
async def test_execute_calls_context_builder(executor, mock_llm, mock_context_builder):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Hi"}
    async for _ in executor.execute("Hi", "session-1", system_prompt="You are a tutor"):
        pass
    mock_context_builder.build_sync.assert_called()
    call_args = mock_context_builder.build_sync.call_args
    assert call_args.kwargs["session_id"] == "session-1"
    assert "tutor" in call_args.kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_execute_adds_turns_to_memory(executor, mock_llm, mock_memory):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Reply"}
    async for _ in executor.execute("Hi", "session-1"):
        pass
    assert mock_memory.add_turn.call_count >= 2  # user turn + assistant turn


@pytest.mark.asyncio
async def test_execute_transitions_state(executor, mock_llm):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Result"}
    states = []
    async for _ in executor.execute("task", "session-1"):
        states.append(executor._state_machine.get_state())
    assert executor._state_machine.get_state() == "done"


@pytest.mark.asyncio
async def test_execute_with_tool_call(executor, mock_llm, mock_memory, mock_context_builder):
    """Verify ReAct loop handles tool calls correctly"""
    # First call returns tool_call, second returns text
    call_count = 0
    async def mock_chat(messages, tools=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "fake_tool",
                        "arguments": '{"input": "test"}',
                    },
                }],
            }
        return {"role": "assistant", "content": "Tool result returned"}

    mock_llm.chat = mock_chat

    # Register a tool with a proper args_schema
    class FakeToolInput(BaseModel):
        input: str

    class FakeToolForTest(BaseTool):
        name: str = "fake_tool"
        description: str = "A fake tool"
        args_schema: type[FakeToolInput] = FakeToolInput

        def _execute_sync(self, tool_input, runtime=None, context=None):
            return {"result": "executed!"}

    executor._tools.register(FakeToolForTest())

    results = []
    async for chunk in executor.execute("use the tool", "session-1"):
        results.append(chunk)

    # Should yield the final text response
    assert "Tool result returned" in "".join(results)
    # LLM should have been called twice (tool + text)
    assert call_count == 2