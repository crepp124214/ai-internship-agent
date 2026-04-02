"""Tracker agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.core.agent.base_agent import BaseAgent
from src.core.llm import BaseLLM, LLMFactory, LLMProviderError
from src.utils.config_loader import get_settings


class TrackerAgentError(RuntimeError):
    """Base error for tracker-agent failures."""


class EmptyTrackerAdviceInputError(TrackerAgentError):
    """Raised when required tracker advice input is missing."""


class TrackerLLMError(TrackerAgentError):
    """Raised when the LLM adapter fails."""


class TrackerAgent(BaseAgent):
    """Generate advice for application tracking next steps."""

    name = "tracker_agent"
    description = "Tracker advice and follow-up planning agent"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        llm: Optional[BaseLLM] = None,
        allow_mock_fallback: bool = False,
    ):
        super().__init__(config)
        self.config = self._merge_runtime_config(self.config)
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
        tracker_yaml = cls._load_yaml_config(root / "configs" / "agents" / "tracker_agent.yaml")
        settings = get_settings()

        default_config = {
            "provider": settings.LLM_PROVIDER,
            "api_key": settings.OPENAI_API_KEY,
            "model": settings_yaml.get("llm", {}).get("default_model"),
            "temperature": settings_yaml.get("llm", {}).get("temperature"),
            "max_tokens": settings_yaml.get("llm", {}).get("max_tokens"),
        }

        tracker_llm = tracker_yaml.get("llm", {})
        default_config.update(
            {
                "provider": tracker_llm.get("provider", default_config.get("provider")),
                "model": tracker_llm.get("model", default_config.get("model")),
                "temperature": tracker_llm.get("temperature", default_config.get("temperature")),
                "max_tokens": tracker_llm.get("max_tokens", default_config.get("max_tokens")),
            }
        )
        return {key: value for key, value in default_config.items() if value is not None}

    @classmethod
    def _merge_runtime_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        merged = cls._load_default_config()
        merged.update(config or {})
        return merged

    def _build_llm(self) -> BaseLLM:
        provider = (self.config.get("provider") or "mock").lower()
        try:
            return LLMFactory.create(provider, self.config)
        except LLMProviderError:
            if provider == "openai" and self.allow_mock_fallback and not self.config.get("api_key"):
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
            / "tracker_agent.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return (
            "Tracker Agent Prompt Pack\n"
            "Use concise, practical language for application follow-up advice.\n"
        )

    @staticmethod
    def _normalize_text(value: str, label: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise EmptyTrackerAdviceInputError(f"{label} is empty")
        return normalized

    def _build_prompt(
        self,
        application_context: str,
        job_context: Optional[str],
        resume_context: Optional[str],
    ) -> str:
        job_line = job_context or "No job context provided."
        resume_line = resume_context or "No resume context provided."
        return (
            f"{self._prompt_pack}\n\n"
            "Task: advise the next best steps for a job application.\n"
            f"Application context: {application_context}\n"
            f"Job context: {job_line}\n"
            f"Resume context: {resume_line}\n"
            "Return:\n"
            "Summary: <one concise paragraph>\n"
            "Next steps:\n"
            "- <step 1>\n"
            "- <step 2>\n"
            "Risks:\n"
            "- <risk 1>\n"
            "- <risk 2>"
        )

    @staticmethod
    def _extract_section_lines(content: str, section_name: str) -> List[str]:
        lines = [line.rstrip() for line in content.splitlines()]
        collecting = False
        collected: List[str] = []
        for raw_line in lines:
            line = raw_line.strip()
            lower_line = line.lower()
            if lower_line.startswith(f"{section_name.lower()}:"):
                collecting = True
                remainder = line.split(":", 1)[1].strip()
                if remainder:
                    collected.append(remainder)
                continue

            if collecting and (
                lower_line.startswith("summary:")
                or lower_line.startswith("next steps:")
                or lower_line.startswith("risks:")
            ):
                break

            if collecting and line:
                collected.append(line)

        cleaned: List[str] = []
        for line in collected:
            value = line.lstrip("-*0123456789. ").strip()
            if value:
                cleaned.append(value)
        return cleaned

    @staticmethod
    def _extract_summary(content: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("summary:"):
                return stripped.split(":", 1)[1].strip()
        return content.strip().splitlines()[0].strip() if content.strip() else ""

    async def advise_next_steps(
        self,
        application_context: str,
        job_context: Optional[str] = None,
        resume_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_application_context = self._normalize_text(
            application_context,
            "application context",
        )
        try:
            content = await self.llm.generate(
                normalized_application_context,
                system_prompt=self._build_prompt(
                    normalized_application_context,
                    job_context,
                    resume_context,
                ),
            )
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise TrackerLLMError("failed to generate tracker advice") from exc

        return {
            "mode": "tracker_advice",
            "application_context": normalized_application_context,
            "job_context": job_context,
            "resume_context": resume_context,
            "summary": self._extract_summary(content),
            "next_steps": self._extract_section_lines(content, "next steps"),
            "risks": self._extract_section_lines(content, "risks"),
            "raw_content": content,
        }

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return await self.advise_next_steps(
            application_context=task.get("application_context") or "",
            job_context=task.get("job_context"),
            resume_context=task.get("resume_context"),
        )
