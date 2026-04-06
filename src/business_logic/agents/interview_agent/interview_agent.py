"""Interview agent implementation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.core.agent.base_agent import BaseAgent
from src.core.llm import BaseLLM, LLMFactory, LLMProviderError
from src.utils.config_loader import get_settings


class InterviewAgentError(RuntimeError):
    """Base error for interview-agent failures."""


class EmptyInterviewInputError(InterviewAgentError):
    """Raised when required interview input is missing."""


class InterviewLLMError(InterviewAgentError):
    """Raised when the LLM adapter fails."""


class InterviewAgent(BaseAgent):
    """Generate interview questions and evaluate answers."""

    name = "interview_agent"
    description = "Interview question generation and answer evaluation agent"

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
        interview_yaml = cls._load_yaml_config(root / "configs" / "agents" / "interview_agent.yaml")
        settings = get_settings()

        default_config = {
            "provider": settings.LLM_PROVIDER,
            "api_key": settings.OPENAI_API_KEY or os.getenv("MINIMAX_API_KEY"),
            "model": settings_yaml.get("llm", {}).get("default_model"),
            "temperature": settings_yaml.get("llm", {}).get("temperature"),
            "max_tokens": settings_yaml.get("llm", {}).get("max_tokens"),
        }

        interview_llm = interview_yaml.get("llm", {})
        default_config.update(
            {
                "provider": interview_llm.get("provider", default_config.get("provider")),
                "api_key": interview_llm.get("api_key") or os.getenv("MINIMAX_API_KEY") or default_config.get("api_key"),
                "base_url": interview_llm.get("base_url") or os.getenv("MINIMAX_BASE_URL"),
                "model": interview_llm.get("model", default_config.get("model")),
                "temperature": interview_llm.get("temperature", default_config.get("temperature")),
                "max_tokens": interview_llm.get("max_tokens", default_config.get("max_tokens")),
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
            / "interview_agent.md"
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return (
            "Interview Agent Prompt Pack\n"
            "Use concise, actionable language for question generation and answer evaluation.\n"
        )

    @staticmethod
    def _normalize_required_text(value: str, label: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise EmptyInterviewInputError(f"{label} is empty")
        return normalized

    def _build_generation_prompt(
        self,
        job_context: str,
        resume_context: Optional[str],
        count: int,
    ) -> str:
        resume_line = resume_context or "No resume context provided."
        return (
            f"{self._prompt_pack}\n\n"
            "Task: generate interview questions.\n"
            f"Question count: {count}\n"
            f"Job context: {job_context}\n"
            f"Resume context: {resume_line}\n"
            "Return one question per line prefixed with 'Question:'."
        )

    def _build_evaluation_prompt(
        self,
        question_text: str,
        user_answer: str,
        job_context: Optional[str],
    ) -> str:
        job_line = job_context or "No job context provided."
        return (
            f"{self._prompt_pack}\n\n"
            "Task: evaluate an interview answer.\n"
            f"Job context: {job_line}\n"
            f"Question: {question_text}\n"
            f"Answer: {user_answer}\n"
            "Return:\n"
            "Score: <0-100>\n"
            "Feedback: <short assessment>"
        )

    @staticmethod
    def _extract_questions(content: str, count: int) -> List[Dict[str, Any]]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        questions: List[Dict[str, Any]] = []
        for index, line in enumerate(lines[:count], start=1):
            question_text = re.sub(r"^Question:\s*", "", line, flags=re.IGNORECASE)
            questions.append(
                {
                    "question_number": index,
                    "question_text": question_text,
                    "question_type": "technical",
                    "difficulty": "medium",
                    "category": "generated",
                }
            )
        return questions

    @staticmethod
    def _extract_score(content: str) -> int:
        match = re.search(r"score:\s*(\d{1,3})", content, flags=re.IGNORECASE)
        if not match:
            return 0
        score = int(match.group(1))
        return max(0, min(score, 100))

    @staticmethod
    def _extract_feedback(content: str) -> str:
        match = re.search(r"feedback:\s*(.+)", content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.strip()

    async def generate_interview_questions(
        self,
        job_context: str,
        resume_context: Optional[str] = None,
        count: int = 5,
    ) -> Dict[str, Any]:
        normalized_job_context = self._normalize_required_text(job_context, "job context")
        try:
            content = await self.llm.generate(
                normalized_job_context,
                system_prompt=self._build_generation_prompt(
                    normalized_job_context,
                    resume_context,
                    count,
                ),
            )
        except Exception as exc:
            raise InterviewLLMError("failed to generate interview questions") from exc

        return {
            "mode": "question_generation",
            "job_context": normalized_job_context,
            "resume_context": resume_context,
            "count": count,
            "questions": self._extract_questions(content, count),
            "raw_content": content,
            "provider": self.config.get("provider") or "mock",
            "model": self.config.get("model") or "unknown",
        }

    async def evaluate_interview_answer(
        self,
        question_text: str,
        user_answer: str,
        job_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_question = self._normalize_required_text(question_text, "question text")
        normalized_answer = self._normalize_required_text(user_answer, "user answer")
        try:
            content = await self.llm.generate(
                normalized_answer,
                system_prompt=self._build_evaluation_prompt(
                    normalized_question,
                    normalized_answer,
                    job_context,
                ),
            )
        except Exception as exc:
            raise InterviewLLMError("failed to evaluate interview answer") from exc

        return {
            "mode": "answer_evaluation",
            "question_text": normalized_question,
            "user_answer": normalized_answer,
            "job_context": job_context,
            "score": self._extract_score(content),
            "feedback": self._extract_feedback(content),
            "raw_content": content,
            "provider": self.config.get("provider") or "mock",
            "model": self.config.get("model") or "unknown",
        }

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = (task.get("action") or "generate").strip().lower()
        if action == "evaluate":
            return await self.evaluate_interview_answer(
                question_text=task.get("question_text") or "",
                user_answer=task.get("user_answer") or "",
                job_context=task.get("job_context"),
            )
        return await self.generate_interview_questions(
            job_context=task.get("job_context") or "",
            resume_context=task.get("resume_context"),
            count=task.get("count", 5),
        )
