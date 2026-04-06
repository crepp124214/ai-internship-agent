import pytest
from unittest.mock import MagicMock, patch

from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.memory_store import Turn, MemoryEntry


@pytest.fixture
def mock_memory():
    memory = MagicMock()
    memory.get_turns = MagicMock(return_value=[
        Turn(role="user", content="I want to customize my resume", timestamp="2026-01-01T00:00:00Z"),
        Turn(role="assistant", content="Please paste your JD", timestamp="2026-01-01T00:00:01Z"),
    ])
    memory.search_memory = MagicMock(return_value=[
        MemoryEntry(id="mem-1", content="user has Python experience", metadata={}, score=0.85),
    ])
    return memory


@pytest.fixture
def builder(mock_memory):
    return ContextBuilder(memory=mock_memory)


def test_build_includes_system_prompt(builder):
    messages = builder.build_sync("session-1", "You are a helpful assistant")
    assert messages[0]["role"] == "system"
    assert "helpful assistant" in messages[0]["content"]


def test_build_includes_turns(builder, mock_memory):
    messages = builder.build_sync("session-1", "You are a helpful assistant")
    roles = [m["role"] for m in messages]
    contents = [m["content"] for m in messages]
    assert "user" in roles
    assert "I want to customize my resume" in contents
    assert "Please paste your JD" in contents


def test_build_includes_memory_results(builder, mock_memory):
    messages = builder.build_sync("session-1", "You are a helpful assistant")
    full_content = " ".join(m["content"] for m in messages)
    assert "Python experience" in full_content


def test_build_respects_max_turns_limit(builder, mock_memory):
    mock_memory.get_turns = MagicMock(return_value=[
        Turn(role="user", content=f"turn {i}", timestamp="2026-01-01T00:00:00Z")
        for i in range(10)
    ])
    messages = builder.build_sync("session-1", "system prompt", max_turns=5)
    user_turns = [m for m in messages if m["role"] == "user"]
    assert len(user_turns) == 5


def test_build_no_memory_below_threshold(builder, mock_memory):
    mock_memory.search_memory = MagicMock(return_value=[
        MemoryEntry(id="mem-1", content="low relevance", metadata={}, score=0.4),
    ])
    messages = builder.build_sync("session-1", "system prompt", memory_threshold=0.7)
    full_content = " ".join(m["content"] for m in messages)
    assert "low relevance" not in full_content