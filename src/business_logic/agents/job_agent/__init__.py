"""Job agent package exports."""

from src.business_logic.agents.job_agent.job_agent import (
    EmptyJobResumeTextError,
    JobAgent,
    JobAgentError,
    JobMatchLLMError,
)

job_agent = JobAgent(allow_mock_fallback=True)

__all__ = [
    "EmptyJobResumeTextError",
    "JobAgent",
    "JobAgentError",
    "JobMatchLLMError",
    "job_agent",
]
