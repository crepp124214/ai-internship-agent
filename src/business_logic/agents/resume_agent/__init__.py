"""Resume agent package exports."""

from src.business_logic.agents.resume_agent.resume_agent import (
    EmptyResumeTextError,
    ResumeAgent,
    ResumeAgentError,
    ResumeLLMError,
)

resume_agent = ResumeAgent(allow_mock_fallback=True)

__all__ = [
    "EmptyResumeTextError",
    "ResumeAgent",
    "ResumeAgentError",
    "ResumeLLMError",
    "resume_agent",
]
