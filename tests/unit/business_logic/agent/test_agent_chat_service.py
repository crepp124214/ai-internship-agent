import pytest
from src.business_logic.agent.agent_chat_service import AgentChatService


class TestAgentChatService:
    def setup_method(self):
        self.service = AgentChatService()

    def test_route_to_jd_customizer(self):
        result = self.service.route_task("帮我定制简历")
        assert result == "jd_customizer"

    def test_route_to_interview_coach(self):
        result = self.service.route_task("我想练习面试")
        assert result == "interview_coach"

    def test_route_to_tracker(self):
        result = self.service.route_task("投递建议")
        assert result == "tracker"

    def test_route_to_generic(self):
        result = self.service.route_task("今天天气怎么样")
        assert result == "generic"

    def test_build_context_from_resume_id(self):
        ctx = self.service.build_context(resume_id=1)
        assert ctx["resume_id"] == 1
        assert "task_type" in ctx
