import pytest
from unittest.mock import AsyncMock, MagicMock
from src.business_logic.interview.interview_coach_agent import InterviewCoachAgent


class TestInterviewCoachAgent:
    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_memory = MagicMock()
        self.mock_memory.search_memory.return_value = []
        self.tool_registry = MagicMock()
        self.agent = InterviewCoachAgent(
            llm=self.mock_llm,
            tool_registry=self.tool_registry,
            memory=self.mock_memory,
        )

    def test_agent_initializes(self):
        assert self.agent._llm is not None
        assert "面试" in self.agent._system_prompt

    @pytest.mark.asyncio
    async def test_generate_coach_flow_returns_opening_and_questions(self):
        self.mock_llm.chat.return_value = {
            "content": "你好，我是字节跳动的面试官。\nQ1: 请描述你最近的项目经历。\nQ2: FastAPI 中间件机制是什么？\nQ3: 如何做数据库优化？",
            "tool_calls": None,
        }
        result = await self.agent.generate_coach_flow(
            job_title="后端开发",
            jd_text="熟悉 Python、FastAPI、PostgreSQL",
            count=3,
        )
        assert "opening" in result
        assert len(result["questions"]) == 3

    @pytest.mark.asyncio
    async def test_generate_coach_flow_supports_block_style_sections(self):
        self.mock_llm.chat.return_value = {
            "content": "【开场白】\n你好，我是后端岗位的面试官。\n\n【问题1】\n请介绍一个你最近做的后端项目。\n【问题2】\n你如何处理异步任务重试？",
            "tool_calls": None,
        }
        result = await self.agent.generate_coach_flow(
            job_title="后端开发",
            jd_text="熟悉 Python、FastAPI、PostgreSQL",
            count=2,
        )
        assert result["opening"] == "你好，我是后端岗位的面试官。"
        assert result["questions"] == [
            "请介绍一个你最近做的后端项目。",
            "你如何处理异步任务重试？",
        ]

    @pytest.mark.asyncio
    async def test_evaluate_single_answer_returns_score_and_feedback(self):
        self.mock_llm.chat.return_value = {
            "content": "Score: 80\nFeedback: 回答清晰，建议补充性能数据。",
            "tool_calls": None,
        }
        result = await self.agent.evaluate_single_answer(
            question="描述你的项目",
            answer="我做了一个电商网站，使用 FastAPI。",
            job_context="Python FastAPI",
        )
        assert result["score"] == 80
        assert "建议" in result["feedback"]

    @pytest.mark.asyncio
    async def test_evaluate_single_answer_uses_non_labeled_feedback_body(self):
        self.mock_llm.chat.return_value = {
            "content": "Score: 69\n你的回答覆盖了后端技术栈和项目职责，但还可以补充更具体的性能指标与系统规模。",
            "tool_calls": None,
        }
        result = await self.agent.evaluate_single_answer(
            question="描述你的项目",
            answer="我做了一个电商网站，使用 FastAPI。",
            job_context="Python FastAPI",
        )
        assert result["score"] == 69
        assert "性能指标" in result["feedback"]
