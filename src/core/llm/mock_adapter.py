"""Deterministic mock LLM adapter used for tests and local development."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from src.core.llm.exceptions import LLMRetryableError
from src.core.llm.retry import retry_async

from src.core.llm.base_llm import BaseLLM


class MockLLMAdapter(BaseLLM):
    """A predictable LLM adapter for offline use."""

    provider = "mock"
    name = "mock_llm"
    description = "Deterministic mock LLM"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model = self.config.get("model", "mock-model")
        # Number of times to fail before succeeding (for retry testing)
        self._fail_times = int(self.config.get("mock_fail_times", 0)) if isinstance(self.config, dict) else 0
        self._attempts = 0

    @retry_async(max_retries=3, base=2, initial=1.0)
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        self._attempts += 1
        if self._attempts <= self._fail_times:
            raise LLMRetryableError("mock transient error for retry")
        if system_prompt:
            return f"mock-generate:{system_prompt.strip()}|{prompt.strip()}"
        return f"mock-generate:{prompt.strip()}"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        last_message = messages[-1]["content"] if messages else ""
        return {"role": "assistant", "content": f"mock-chat:{last_message.strip()}"}

    async def get_embedding(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [round(digest[index] / 255.0, 6) for index in range(3)]
