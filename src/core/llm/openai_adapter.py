"""OpenAI adapter implementation."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from src.core.llm.exceptions import LLMRetryableError, CircuitBreakerOpenError
from src.core.llm.circuit_breaker import CircuitBreaker
from src.core.llm.retry import retry_async

from openai import AsyncOpenAI

from src.core.llm.base_llm import BaseLLM
from src.core.llm.exceptions import LLMConfigurationError, LLMRequestError


class OpenAIAdapter(BaseLLM):
    """Adapter that talks to the OpenAI Async client."""

    provider = "openai"
    name = "openai_llm"
    description = "OpenAI-compatible LLM adapter"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self._resolve_api_key()
        self.model = self._resolve_option("model", "gpt-4", env_var="OPENAI_MODEL")
        self.temperature = self._resolve_float_option(
            "temperature",
            0.7,
            env_var="OPENAI_TEMPERATURE",
        )
        self.max_tokens = self._resolve_int_option(
            "max_tokens",
            None,
            env_var="OPENAI_MAX_TOKENS",
        )
        self.timeout = self._resolve_timeout_option("timeout", None, env_var="OPENAI_TIMEOUT")
        self.max_retries = self._resolve_int_option(
            "max_retries",
            None,
            env_var="OPENAI_MAX_RETRIES",
        )

        # Optional circuit breaker injection from config
        cb = None
        if isinstance(self.config, dict):
            cb = self.config.get("circuit_breaker")
        self.circuit_breaker: Optional[CircuitBreaker] = cb

        client_kwargs = self._build_client_kwargs()
        try:
            self.client = AsyncOpenAI(api_key=self.api_key, **client_kwargs)
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise LLMConfigurationError("failed to initialize OpenAI client") from exc

    @staticmethod
    def _has_config_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True

    def _resolve_option(self, key: str, default: Any, env_var: Optional[str] = None) -> Any:
        value = self.config.get(key)
        if self._has_config_value(value):
            return value

        nested_llm = self.config.get("llm")
        if isinstance(nested_llm, dict):
            nested_value = nested_llm.get(key)
            if self._has_config_value(nested_value):
                return nested_value

        if env_var:
            env_value = os.getenv(env_var)
            if self._has_config_value(env_value):
                return env_value
        return default

    def _resolve_first_valid_option(
        self,
        key: str,
        default: Any,
        coercer,
        env_var: Optional[str] = None,
    ) -> Any:
        candidates = [self.config.get(key)]

        nested_llm = self.config.get("llm")
        if isinstance(nested_llm, dict):
            candidates.append(nested_llm.get(key))

        if env_var:
            candidates.append(os.getenv(env_var))

        for candidate in candidates:
            if not self._has_config_value(candidate):
                continue
            coerced = coercer(candidate)
            if coerced is not None:
                return coerced

        return default

    def _resolve_float_option(
        self,
        key: str,
        default: Optional[float],
        env_var: Optional[str] = None,
    ) -> Optional[float]:
        return self._resolve_first_valid_option(key, default, self._coerce_float, env_var=env_var)

    def _resolve_int_option(
        self,
        key: str,
        default: Optional[int],
        env_var: Optional[str] = None,
    ) -> Optional[int]:
        return self._resolve_first_valid_option(key, default, self._coerce_int, env_var=env_var)

    def _resolve_timeout_option(
        self,
        key: str,
        default: Optional[Any],
        env_var: Optional[str] = None,
    ) -> Optional[Any]:
        return self._resolve_first_valid_option(key, default, self._coerce_timeout, env_var=env_var)

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return float(stripped)
            except ValueError:
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value) if value.is_integer() else None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                numeric_value = float(stripped)
            except ValueError:
                return None
            return int(numeric_value) if numeric_value.is_integer() else None
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None
        return int(numeric_value) if numeric_value.is_integer() else None

    @staticmethod
    def _coerce_timeout(value: Any) -> Optional[Any]:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                numeric_value = float(stripped)
            except ValueError:
                return None
            return int(numeric_value) if numeric_value.is_integer() else numeric_value
        return value

    def _resolve_api_key(self) -> str:
        api_key = self._resolve_option("api_key", None, env_var="OPENAI_API_KEY")
        if not api_key:
            raise LLMConfigurationError("OpenAI API key is required")
        return str(api_key)

    def _build_client_kwargs(self) -> Dict[str, Any]:
        client_kwargs: Dict[str, Any] = {}
        for key in (
            "base_url",
            "organization",
            "project",
            "timeout",
            "max_retries",
            "default_headers",
            "default_query",
            "http_client",
            "_strict_response_validation",
        ):
            if key == "timeout":
                value = self.timeout
            elif key == "max_retries":
                value = self.max_retries
            else:
                env_var = "OPENAI_BASE_URL" if key == "base_url" else None
                value = self._resolve_option(key, None, env_var=env_var)
            if value is not None:
                client_kwargs[key] = value
        return client_kwargs

    @staticmethod
    def _extract_chat_content(response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise LLMRequestError("OpenAI chat response did not contain choices")

        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if content is None:
            raise LLMRequestError("OpenAI chat response did not contain message content")
        return str(content)

    @staticmethod
    def _extract_text_content(response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text is not None:
            return str(output_text)

        output = getattr(response, "output", None) or []
        for item in output:
            content_items = getattr(item, "content", None) or []
            for content_item in content_items:
                text = getattr(content_item, "text", None)
                if text is not None:
                    return str(text)

        raise LLMRequestError("OpenAI text generation response did not contain output text")

    @staticmethod
    def _extract_embedding(response: Any) -> List[float]:
        data = getattr(response, "data", None) or []
        if not data:
            raise LLMRequestError("OpenAI embedding response did not contain vectors")

        embedding = getattr(data[0], "embedding", None)
        if embedding is None:
            raise LLMRequestError("OpenAI embedding response did not contain embedding data")

        return [float(value) for value in embedding]

    async def _run_text_generation(self, **kwargs: Any) -> Any:
        try:
            return await self.client.responses.create(**kwargs)
        except LLMRequestError:
            raise
        except Exception as exc:  # pragma: no cover - defensive conversion
            try:
                from openai import error as openai_error
            except Exception:
                openai_error = None  # type: ignore
            if (
                openai_error is not None
                and isinstance(exc, (openai_error.RateLimitError, ConnectionError, TimeoutError))
            ):
                raise LLMRetryableError("Transient OpenAI text generation error") from exc
            raise LLMRequestError("OpenAI text generation failed") from exc

    async def _run_chat_completion(self, **kwargs: Any) -> Any:
        try:
            return await self.client.chat.completions.create(**kwargs)
        except LLMRequestError:
            raise
        except Exception as exc:  # pragma: no cover - defensive conversion
            try:
                from openai import error as openai_error
            except Exception:
                openai_error = None  # type: ignore
            if (
                openai_error is not None
                and isinstance(exc, (openai_error.RateLimitError, ConnectionError, TimeoutError))
            ):
                raise LLMRetryableError("Transient OpenAI chat error") from exc
            raise LLMRequestError("OpenAI chat request failed") from exc

    async def _run_embedding_request(self, **kwargs: Any) -> Any:
        try:
            return await self.client.embeddings.create(**kwargs)
        except LLMRequestError:
            raise
        except Exception as exc:  # pragma: no cover - defensive conversion
            try:
                from openai import error as openai_error
            except Exception:
                openai_error = None  # type: ignore
            if (
                openai_error is not None
                and isinstance(exc, (openai_error.RateLimitError, ConnectionError, TimeoutError))
            ):
                raise LLMRetryableError("Transient OpenAI embedding error") from exc
            raise LLMRequestError("OpenAI embedding request failed") from exc

    @retry_async(max_retries=3, base=2, initial=1.0)
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        # Circuit Breaker: block or probe before making a request
        if self.circuit_breaker is not None:
            await self.circuit_breaker.allow_request()

        input_messages: List[Dict[str, str]] = []
        if system_prompt:
            input_messages.append({"role": "system", "content": system_prompt})
        input_messages.append({"role": "user", "content": prompt})

        try:
            resolved_temperature = self._coerce_float(temperature)
            if resolved_temperature is None:
                resolved_temperature = self.temperature

            resolved_max_tokens = self._coerce_int(max_tokens)
            if resolved_max_tokens is None:
                resolved_max_tokens = self.max_tokens

            response = await self._run_text_generation(
                model=self.model,
                input=input_messages,
                temperature=resolved_temperature,
                max_output_tokens=resolved_max_tokens,
                **kwargs,
            )
            if self.circuit_breaker is not None:
                await self.circuit_breaker.on_success()
        except Exception:
            if self.circuit_breaker is not None:
                await self.circuit_breaker.on_failure()
            raise
        return self._extract_text_content(response)

    @retry_async(max_retries=3, base=2, initial=1.0)
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if self.circuit_breaker is not None:
            await self.circuit_breaker.allow_request()

        try:
            resolved_temperature = self._coerce_float(temperature)
            if resolved_temperature is None:
                resolved_temperature = self.temperature

            resolved_max_tokens = self._coerce_int(max_tokens)
            if resolved_max_tokens is None:
                resolved_max_tokens = self.max_tokens

            response = await self._run_chat_completion(
                model=self.model,
                messages=messages,
                temperature=resolved_temperature,
                max_tokens=resolved_max_tokens,
                **kwargs,
            )
            if self.circuit_breaker is not None:
                await self.circuit_breaker.on_success()
        except Exception:
            if self.circuit_breaker is not None:
                await self.circuit_breaker.on_failure()
            raise
        return {"role": "assistant", "content": self._extract_chat_content(response)}

    @retry_async(max_retries=3, base=2, initial=1.0)
    async def get_embedding(self, text: str) -> List[float]:
        if self.circuit_breaker is not None:
            await self.circuit_breaker.allow_request()
        try:
            response = await self._run_embedding_request(
                model=self.model,
                input=text,
            )
            if self.circuit_breaker is not None:
                await self.circuit_breaker.on_success()
        except Exception:
            if self.circuit_breaker is not None:
                await self.circuit_breaker.on_failure()
            raise
        return self._extract_embedding(response)
