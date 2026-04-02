import asyncio
import pytest

from src.core.llm.mock_adapter import MockLLMAdapter
from src.core.llm.exceptions import LLMRetryableError


@pytest.mark.asyncio
async def test_mock_adapter_retry_until_success():
    # Configure mock to fail first 2 times, then succeed
    cfg = {"mock_fail_times": 2, "model": "mock-model"}
    adapter = MockLLMAdapter(cfg)

    # First call should trigger 3 attempts via retry decorator
    result = await adapter.generate("hello world")
    assert isinstance(result, str)
    assert result.startswith("mock-generate:")
