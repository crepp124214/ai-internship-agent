import pytest

from src.core.agent.base_agent import BaseAgent


class TestBaseAgent:
    def setup_method(self):
        self.agent_config = {
            "name": "test_agent",
            "description": "Test Agent",
        }

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        class MockAgent(BaseAgent):
            async def execute(self, task):
                return {"result": "success"}

        agent = MockAgent(self.agent_config)
        assert agent.config == self.agent_config
        assert not agent._is_initialized

        await agent.initialize()
        assert agent._is_initialized

    @pytest.mark.asyncio
    async def test_agent_cleanup(self):
        class MockAgent(BaseAgent):
            async def execute(self, task):
                return {"result": "success"}

        agent = MockAgent(self.agent_config)
        await agent.initialize()
        await agent.cleanup()
        assert not agent._is_initialized

    def test_agent_get_status(self):
        class MockAgent(BaseAgent):
            async def execute(self, task):
                return {"result": "success"}

        agent = MockAgent(self.agent_config)
        status = agent.get_status()
        assert status["name"] == BaseAgent.name
        assert status["description"] == BaseAgent.description
        assert not status["initialized"]

    @pytest.mark.asyncio
    async def test_agent_execute(self):
        class MockAgent(BaseAgent):
            async def execute(self, task):
                return {"result": task.get("content")}

        agent = MockAgent(self.agent_config)
        result = await agent.execute({"content": "test task"})
        assert result["result"] == "test task"
