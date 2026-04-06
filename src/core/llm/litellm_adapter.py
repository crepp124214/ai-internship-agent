"""
LiteLLM 统一 adapter
通过 litellm 调用所有主流 LLM provider，统一接口
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock

import litellm
from litellm import acompletion, aembedding

from src.core.llm.exceptions import LLMRequestError

# 禁止 litellm 的默认重试（adapter 自带 retry 机制）
litellm.max_retries = 0
litellm.num_retries = 0


class LiteLLMAdapter:
    """
    通过 LiteLLM 调用所有 LLM provider，统一 chat 接口。
    与旧 LLMFactory/LLMAdapter 解耦，专供 Agent Runtime 使用。
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.api_key = api_key or litellm.api_key
        self.base_url = base_url
        self.api_version = api_version
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._extra_kwargs = kwargs

    def _build_litellm_params(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **self._extra_kwargs,
            **kwargs,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.base_url:
            params["base_url"] = self.base_url
        if self.api_version:
            params["api_version"] = self.api_version
        if self.timeout:
            params["timeout"] = self.timeout
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        return params

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        发送 chat 请求，返回 {"role": "assistant", "content": str}
        如果 LLM 返回 tool_call，返回 {"role": "assistant", "tool_calls": [...]}
        """
        params = self._build_litellm_params(messages, tools, tool_choice, **kwargs)
        try:
            response = await acompletion(**params)
        except Exception as exc:
            raise LLMRequestError(f"LiteLLM chat failed: {exc}") from exc

        choices = getattr(response, "choices", [])
        if not choices:
            raise LLMRequestError("LiteLLM response has no choices")

        choice = choices[0]
        message = getattr(choice, "message", None)
        if message is None:
            raise LLMRequestError("LiteLLM response choice has no message")

        result: Dict[str, Any] = {
            "role": getattr(message, "role", "assistant"),
            "content": getattr(message, "content", ""),
        }

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls is not None:
            result["tool_calls"] = [
                {
                    "id": getattr(tc, "id", ""),
                    "type": getattr(tc, "type", "function"),
                    "function": {
                        "name": getattr(getattr(tc, "function", None) or MagicMock(), "name", ""),
                        "arguments": getattr(getattr(tc, "function", None) or MagicMock(), "arguments", "{}"),
                    },
                }
                for tc in tool_calls
            ]

        return result

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """单轮生成，用 prompt + 可选 system_prompt"""
        msgs: List[Dict[str, Any]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})

        result = await self.chat(msgs, **kwargs)
        return result.get("content", "")

    async def get_embedding(self, text: str, **kwargs: Any) -> List[float]:
        """通过 LiteLLM 获取文本 embedding"""
        try:
            response = await aembedding(
                model="text-embedding-3-small",
                input=text,
                api_key=self.api_key,
                base_url=self.base_url,
                **kwargs,
            )
        except Exception as exc:
            raise LLMRequestError(f"LiteLLM embedding failed: {exc}") from exc

        data = getattr(response, "data", [])
        if not data:
            raise LLMRequestError("LiteLLM embedding response has no data")
        embedding = getattr(data[0], "embedding", None)
        if embedding is None:
            raise LLMRequestError("LiteLLM embedding has no vector")
        return [float(x) for x in embedding]