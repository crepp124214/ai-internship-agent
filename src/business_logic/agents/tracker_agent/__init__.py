"""Tracker agent package exports."""

from src.business_logic.agents.tracker_agent.tracker_agent import (
    EmptyTrackerAdviceInputError,
    TrackerAgent,
    TrackerAgentError,
    TrackerLLMError,
)

tracker_agent = TrackerAgent(allow_mock_fallback=True)

__all__ = [
    "EmptyTrackerAdviceInputError",
    "TrackerAgent",
    "TrackerAgentError",
    "TrackerLLMError",
    "tracker_agent",
]
