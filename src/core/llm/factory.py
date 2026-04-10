"""Factory helpers for constructing LLM adapters."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from src.core.llm.base_llm import BaseLLM
from src.core.llm.exceptions import LLMProviderError
from src.core.llm.mock_adapter import MockLLMAdapter
from src.core.llm.openai_adapter import OpenAIAdapter
from src.utils.config_loader import get_settings


class LLMFactory:
    """Create an LLM adapter from provider configuration."""

    @staticmethod
    def create(
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseLLM:
        adapter_config = dict(config or {})
        nested_llm_config = adapter_config.get("llm")
        if isinstance(nested_llm_config, dict):
            merged_config = {**nested_llm_config, **adapter_config}
        else:
            merged_config = dict(adapter_config)

        provider_name = LLMFactory._resolve_provider(provider, merged_config)
        merged_config["provider"] = provider_name

        if provider_name in {"mock", "stub"}:
            return MockLLMAdapter(merged_config)
        if provider_name in {"openai", "minimax", "zhipu"}:
            return OpenAIAdapter(merged_config)
        raise LLMProviderError(f"Unsupported LLM provider: {provider_name}")

    @staticmethod
    def _resolve_provider(
        provider: Optional[str],
        config: Dict[str, Any],
    ) -> str:
        provider_name = (provider or "").strip().lower()
        if provider_name:
            return provider_name

        config_provider = str(config.get("provider") or "").strip().lower()
        if config_provider:
            return config_provider

        nested_llm = config.get("llm")
        if isinstance(nested_llm, dict):
            nested_provider = str(nested_llm.get("provider") or "").strip().lower()
            if nested_provider:
                return nested_provider

        default_provider = LLMFactory._resolve_default_provider()
        if default_provider:
            return default_provider

        return "mock"

    @staticmethod
    def _resolve_default_provider() -> str:
        env_provider = str(os.getenv("LLM_PROVIDER") or "").strip().lower()
        if env_provider:
            return env_provider

        try:
            settings = get_settings()
        except Exception:
            return "mock"

        settings_provider = str(getattr(settings, "LLM_PROVIDER", "") or "").strip().lower()
        if settings_provider:
            return settings_provider

        return "mock"
