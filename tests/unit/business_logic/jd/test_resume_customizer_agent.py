# tests/unit/business_logic/jd/test_resume_customizer_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.business_logic.jd.resume_customizer_agent import ResumeCustomizerAgent
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry


class TestResumeCustomizerAgent:
    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_memory = MagicMock(spec=MemoryStore)
        self.mock_memory.search_memory.return_value = []
        self.tool_registry = ToolRegistry()

    def test_agent_initializes(self):
        agent = ResumeCustomizerAgent(
            llm=self.mock_llm,
            tool_registry=self.tool_registry,
            memory=self.mock_memory,
        )
        assert agent._llm is not None
        assert agent._tool_registry is not None

    def test_agent_has_correct_system_prompt(self):
        agent = ResumeCustomizerAgent(
            llm=self.mock_llm,
            tool_registry=self.tool_registry,
            memory=self.mock_memory,
        )
        assert "简历顾问" in agent._system_prompt or "resume" in agent._system_prompt.lower()