"""Resume agent implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.agent.base_agent import BaseAgent
from src.core.llm import BaseLLM, LLMFactory, LLMProviderError
from src.utils.config_loader import get_settings


class ResumeAgentError(RuntimeError):
    """Base error for resume-agent failures."""


class EmptyResumeTextError(ResumeAgentError):
    """Raised when resume text is missing or blank."""


class ResumeLLMError(ResumeAgentError):
    """Raised when the LLM adapter fails."""


class ResumeAgent(BaseAgent):
    """Generate resume summaries and improvement suggestions."""

    name = "resume_agent"
    description = "Resume analysis and optimization agent"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        llm: Optional[BaseLLM] = None,
        allow_mock_fallback: bool = False,
        user_id: Optional[int] = None,
    ):
        super().__init__(config)
        self.config = self._merge_runtime_config(self.config, user_id=user_id)
        self.allow_mock_fallback = allow_mock_fallback
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
        resume_yaml = cls._load_yaml_config(root / "configs" / "agents" / "resume_agent.yaml")
        settings = get_settings()

        default_config = {
            "provider": settings.LLM_PROVIDER,
            "api_key": settings.OPENAI_API_KEY or os.getenv("MINIMAX_API_KEY"),
            "model": settings_yaml.get("llm", {}).get("default_model"),
            "temperature": settings_yaml.get("llm", {}).get("temperature"),
            "max_tokens": settings_yaml.get("llm", {}).get("max_tokens"),
        }

        resume_llm = resume_yaml.get("llm", {})
        default_config.update(
            {
                "provider": resume_llm.get("provider", default_config.get("provider")),
                "api_key": resume_llm.get("api_key") or os.getenv("MINIMAX_API_KEY") or default_config.get("api_key"),
                "base_url": resume_llm.get("base_url") or os.getenv("MINIMAX_BASE_URL"),
                "model": resume_llm.get("model", default_config.get("model")),
                "temperature": resume_llm.get("temperature", default_config.get("temperature")),
                "max_tokens": resume_llm.get("max_tokens", default_config.get("max_tokens")),
            }
        )
        return {key: value for key, value in default_config.items() if value is not None}

    @classmethod
    def _merge_runtime_config(cls, config: Optional[Dict[str, Any]], user_id: Optional[int] = None) -> Dict[str, Any]:
        merged = cls._load_default_config()
        merged.update(config or {})

        # 查询用户自定义配置，优先使用
        if user_id is not None:
            from src.business_logic.user_llm_config_service import user_llm_config_service
            from src.data_access.database import SessionLocal
            db = SessionLocal()
            try:
                user_config = user_llm_config_service.get_config_for_agent(db, user_id, "resume_agent")
                if user_config:
                    merged.update(user_config)
            finally:
                db.close()

        return {key: value for key, value in merged.items() if value is not None}

    def _build_llm(self) -> BaseLLM:
        provider = (self.config.get("provider") or "mock").lower()
        try:
            return LLMFactory.create(provider, self.config)
        except (LLMProviderError, Exception):
            if self.allow_mock_fallback:
                fallback_config = dict(self.config)
                fallback_config["provider"] = "mock"
                fallback_config.pop("api_key", None)
                self.config = fallback_config
                return LLMFactory.create("mock", fallback_config)
            raise

    @staticmethod
    def _load_prompt_pack() -> str:
        prompt_path = (
            Path(__file__).resolve().parents[4]
            / "docs"
            / "prompts"
            / "resume_agent.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return (
            "Resume Agent Prompt Pack\n"
            "Use concise, actionable language for resume analysis.\n"
        )

    @staticmethod
    def _normalize_text(resume_text: str) -> str:
        normalized = (resume_text or "").strip()
        if not normalized:
            raise EmptyResumeTextError("resume text is empty")
        return normalized

    def _build_system_prompt(self, mode: str, target_role: Optional[str]) -> str:
        role_line = f"Target role: {target_role}" if target_role else "Target role: unspecified"
        task_line = (
            "Task: extract a concise resume summary."
            if mode == "summary"
            else "Task: suggest concrete resume improvements."
        )
        return f"{self._prompt_pack}\n\n{task_line}\n{role_line}"

    async def extract_resume_summary(
        self,
        resume_text: str,
        target_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        text = self._normalize_text(resume_text)
        try:
            content = await self.llm.generate(
                text,
                system_prompt=self._build_system_prompt("summary", target_role),
            )
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise ResumeLLMError("failed to generate resume summary") from exc
        return {
            "mode": "summary",
            "resume_text": text,
            "target_role": target_role,
            "content": content,
            "raw_content": content,
            "provider": self.config.get("provider") or "mock",
            "model": self.config.get("model") or "unknown",
        }

    async def suggest_resume_improvements(
        self,
        resume_text: str,
        target_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        text = self._normalize_text(resume_text)
        try:
            content = await self.llm.generate(
                text,
                system_prompt=self._build_system_prompt("improvements", target_role),
            )
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise ResumeLLMError("failed to generate resume improvements") from exc
        return {
            "mode": "improvements",
            "resume_text": text,
            "target_role": target_role,
            "content": content,
            "raw_content": content,
            "provider": self.config.get("provider") or "mock",
            "model": self.config.get("model") or "unknown",
        }

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = (task.get("action") or "summary").strip().lower()
        resume_text = task.get("resume_text") or task.get("processed_content") or ""
        target_role = task.get("target_role")

        if action == "improvements":
            return await self.suggest_resume_improvements(
                resume_text,
                target_role=target_role,
            )
        return await self.extract_resume_summary(
            resume_text,
            target_role=target_role,
        )
