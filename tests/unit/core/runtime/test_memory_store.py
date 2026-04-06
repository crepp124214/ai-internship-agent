import pytest
from unittest.mock import MagicMock

from src.core.runtime.memory_store import MemoryStore, Turn, MemoryEntry


@pytest.fixture
def mock_redis():
    return MagicMock()


@pytest.fixture
def mock_chroma():
    return MagicMock()


@pytest.fixture
def memory(mock_redis, mock_chroma):
    store = MemoryStore(redis_client=mock_redis, chroma_client=mock_chroma)
    return store


def test_add_turn_stores_in_redis(memory, mock_redis):
    memory.add_turn("session-1", "user", "hello")
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once()


def test_get_turns_returns_reversed_order(memory, mock_redis):
    mock_redis.lrange.return_value = [
        '{"role": "user", "content": "hi", "timestamp": "2026-01-01T00:00:00Z"}',
        '{"role": "assistant", "content": "hello", "timestamp": "2026-01-01T00:00:01Z"}',
    ]
    turns = memory.get_turns("session-1")
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[0].content == "hi"
    assert turns[1].role == "assistant"


def test_add_memory_calls_chroma(memory, mock_chroma):
    mock_collection = MagicMock()
    mock_chroma.get_collection.return_value = mock_collection
    memory.add_memory("session-1", "user submitted resume", {"source": "resume"})
    mock_collection.add.assert_called_once()
    call_args = mock_collection.add.call_args
    assert "user submitted resume" in call_args.kwargs["documents"]


def test_search_memory_returns_filtered_results(memory, mock_chroma):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["mem-1"]],
        "documents": [["resume experience with Python"]],
        "metadatas": [[{"source": "resume"}]],
        "distances": [[0.3]],  # L2 distance
    }
    mock_chroma.get_collection.return_value = mock_collection
    results = memory.search_memory("Python experience", session_id="session-1", threshold=0.5)
    assert len(results) == 1
    # similarity = 1 - 0.3 = 0.7, which is >= 0.5 threshold
    assert results[0].score == 0.7
    assert "Python" in results[0].content


def test_search_memory_filters_by_threshold(memory, mock_chroma):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["mem-1", "mem-2"]],
        "documents": [["relevant content"], ["less relevant content"]],
        "metadatas": [[{}], {}],
        "distances": [[0.2], [0.9]],  # L2 distances
    }
    mock_chroma.get_collection.return_value = mock_collection
    results = memory.search_memory("query", threshold=0.7)
    # similarity(0.2) = 0.8 >= 0.7 → included; similarity(0.9) = 0.1 < 0.7 → filtered
    assert len(results) == 1
    assert results[0].score == 0.8


def test_clear_session_removes_redis_keys(memory, mock_redis):
    memory.clear_session("session-1")
    mock_redis.delete.assert_called()


def test_turn_namedtuple_fields():
    turn = Turn(role="user", content="hi", timestamp="2026-01-01T00:00:00Z")
    assert turn.role == "user"
    assert turn.content == "hi"


def test_memory_entry_namedtuple_fields():
    entry = MemoryEntry(id="mem-1", content="hello", metadata={"k": "v"}, score=0.5)
    assert entry.id == "mem-1"
    assert entry.score == 0.5