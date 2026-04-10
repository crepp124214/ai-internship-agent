"""Job agent implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.agent.base_agent import BaseAgent
from src.core.llm import BaseLLM, LLMFactory, LLMProviderError
from src.core.llm.exceptions import LLMRequestError
from src.utils.config_loader import get_settings


class JobAgentError(RuntimeError):
    """Base error for job-agent failures."""


class EmptyJobResumeTextError(JobAgentError):
    """Raised when job or resume text is missing."""


class JobMatchLLMError(JobAgentError):
    """Raised when the LLM adapter fails."""


class JobAgent(BaseAgent):
    """Match a resume to a job posting."""

    name = "job_agent"
    description = "Job matching and fit evaluation agent"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        llm: Optional[BaseLLM] = None,
        allow_mock_fallback: bool = False,
        user_id: Optional[int] = None,
        user_llm_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self.config = self._merge_runtime_config(
            self.config,
            user_id=user_id,
            user_llm_config=user_llm_config,
        )
        self.allow_mock_fallback = allow_mock_fallback
        self._active_provider = self.config.get("provider") or "mock"
        self.llm = llm or self._build_llm()
        self._prompt_pack = self._load_prompt_pack()

    @classmethod
    def _load_yaml_config(cls, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file) or {}

    @classmethod
    def _load_default_config(cls) -> Dict[str, Any]:
        root = Path(__file__).resolve().parents[4]
        settings_yaml = cls._load_yaml_config(root / "configs" / "settings.yaml")
        job_yaml = cls._load_yaml_config(root / "configs" / "agents" / "job_agent.yaml")
        settings = get_settings()

        default_config = {
            "provider": settings.LLM_PROVIDER,
            "api_key": settings.OPENAI_API_KEY or os.getenv("MINIMAX_API_KEY"),
            "model": settings_yaml.get("llm", {}).get("default_model"),
            "temperature": settings_yaml.get("llm", {}).get("temperature"),
            "max_tokens": settings_yaml.get("llm", {}).get("max_tokens"),
        }

        job_llm = job_yaml.get("llm", {})
        default_config.update(
            {
                "provider": job_llm.get("provider", default_config.get("provider")),
                "api_key": job_llm.get("api_key") or os.getenv("MINIMAX_API_KEY") or default_config.get("api_key"),
                "base_url": job_llm.get("base_url") or os.getenv("MINIMAX_BASE_URL"),
                "model": job_llm.get("model", default_config.get("model")),
                "temperature": job_llm.get("temperature", default_config.get("temperature")),
                "max_tokens": job_llm.get("max_tokens", default_config.get("max_tokens")),
            }
        )
        return {key: value for key, value in default_config.items() if value is not None}

    @classmethod
    def _merge_runtime_config(
        cls,
        config: Optional[Dict[str, Any]],
        user_id: Optional[int] = None,
        user_llm_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        merged = cls._load_default_config()
        merged.update(config or {})

        # 优先使用传入的 user_llm_config（由 service 层获取，避免在 agent 构造函数中同步 DB 调用）
        if user_llm_config:
            merged.update(user_llm_config)

        return {key: value for key, value in merged.items() if value is not None}

    def _build_llm(self) -> BaseLLM:
        provider = (self.config.get("provider") or "mock").lower()
        try:
            return LLMFactory.create(provider, self.config)
        except (LLMProviderError, Exception):
            if self.allow_mock_fallback:
                return self._create_fallback_llm()
            raise

    def _create_fallback_llm(self) -> BaseLLM:
        """Create a fresh mock LLM adapter for fallback, updating _active_provider."""
        fallback_config = dict(self.config)
        fallback_config["provider"] = "mock"
        fallback_config.pop("api_key", None)
        self._active_provider = "mock"
        return LLMFactory.create("mock", fallback_config)

    @staticmethod
    def _load_prompt_pack() -> str:
        prompt_path = (
            Path(__file__).resolve().parents[4]
            / "docs"
            / "prompts"
            / "job_agent.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return (
            "Job Agent Prompt Pack\n"
            "Use concise, practical language for job and resume matching.\n"
        )

    @staticmethod
    def _normalize_required_text(value: str, label: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise EmptyJobResumeTextError(f"{label} is empty")
        return normalized

    def _build_prompt(self, job_context: str, resume_context: str) -> str:
        return (
            f"{self._prompt_pack}\n\n"
            "Task: evaluate how well a resume fits a job.\n"
            f"Job context: {job_context}\n"
            f"Resume context: {resume_context}\n"
            "Return:\n"
            "Score: <0-100>\n"
            "Feedback: <short assessment>"
        )

    @staticmethod
    def _extract_score(content: str) -> int:
        import re

        match = re.search(r"score:\s*(\d{1,3})", content, flags=re.IGNORECASE)
        if not match:
            return 0
        return max(0, min(int(match.group(1)), 100))

    @staticmethod
    def _extract_feedback(content: str) -> str:
        import re

        match = re.search(r"feedback:\s*(.+)", content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.strip()

    async def match_job_to_resume(
        self,
        job_context: str,
        resume_context: str,
    ) -> Dict[str, Any]:
        normalized_job_context = self._normalize_required_text(job_context, "job context")
        normalized_resume_context = self._normalize_required_text(
            resume_context,
            "resume text",
        )
        try:
            content = await self.llm.generate(
                normalized_resume_context,
                system_prompt=self._build_prompt(
                    normalized_job_context,
                    normalized_resume_context,
                ),
            )
        except (LLMRequestError, Exception) as exc:  # pragma: no cover - defensive conversion
            if self.allow_mock_fallback:
                # API 调用失败时，创建 fresh fallback adapter 并重试
                self.llm = self._create_fallback_llm()
                fallback_content = await self.llm.generate(
                    normalized_resume_context,
                    system_prompt=self._build_prompt(
                        normalized_job_context,
                        normalized_resume_context,
                    ),
                )
                return {
                    "mode": "job_match",
                    "job_context": normalized_job_context,
                    "resume_context": normalized_resume_context,
                    "score": self._extract_score(fallback_content),
                    "feedback": self._extract_feedback(fallback_content),
                    "raw_content": fallback_content,
                    "provider": self._active_provider or "mock",
                    "model": self.config.get("model") or "unknown",
                    "status": "fallback",
                    "fallback_used": True,
                }
            raise JobMatchLLMError("failed to match job and resume") from exc

        return {
            "mode": "job_match",
            "job_context": normalized_job_context,
            "resume_context": normalized_resume_context,
            "score": self._extract_score(content),
            "feedback": self._extract_feedback(content),
            "raw_content": content,
            "provider": self._active_provider or "mock",
            "model": self.config.get("model") or "unknown",
            "status": "success",
            "fallback_used": False,
        }

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return await self.match_job_to_resume(
            job_context=task.get("job_context") or "",
            resume_context=task.get("resume_context") or "",
        )
