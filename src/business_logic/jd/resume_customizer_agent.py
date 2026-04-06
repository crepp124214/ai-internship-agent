# src/business_logic/jd/resume_customizer_agent.py
"""AI 简历定制 Agent — 基于 AgentExecutor ReAct 循环"""

from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.tool_registry import ToolRegistry


class ResumeCustomizerAgent:
    """
    基于 AgentExecutor 的简历定制 Agent
    使用 ReAct 循环：read_resume → match_resume_to_job → 生成定制内容
    """

    def __init__(
        self,
        llm: LiteLLMAdapter,
        tool_registry: ToolRegistry,
        memory: MemoryStore,
    ):
        self._llm = llm
        self._tool_registry = tool_registry
        self._memory = memory
        self._system_prompt = (
            "你是一位资深简历顾问，擅长根据目标岗位定制简历内容。\n"
            "你的任务是根据提供的简历和岗位信息，生成一份针对该岗位优化的简历内容。\n"
            "输出格式：纯文本 Markdown，突出简历中与目标岗位最相关的经历和技能。"
        )
        self._state_machine = StateMachine()
        self._context_builder = ContextBuilder(memory=memory)
        self._executor = AgentExecutor(
            llm=llm,
            tools=tool_registry,
            memory=memory,
            state_machine=self._state_machine,
            context_builder=self._context_builder,
        )

    async def customize(
        self,
        resume_id: int,
        jd_id: int,
        custom_instructions: str | None,
        session_id: str,
    ) -> str:
        """
        执行简历定制，返回定制后的简历文本。
        通过 AgentExecutor.execute() 运行 ReAct 循环。
        """
        user_message = self._build_user_message(resume_id, jd_id, custom_instructions)

        full_text = ""
        async for chunk in self._executor.execute(
            task=user_message,
            session_id=session_id,
            system_prompt=self._system_prompt,
        ):
            full_text += chunk

        return full_text

    def _build_user_message(
        self, resume_id: int, jd_id: int, custom_instructions: str | None
    ) -> str:
        msg = (
            f"请帮我定制一份简历。\n"
            f"简历 ID：{resume_id}\n"
            f"目标岗位 JD ID：{jd_id}\n"
        )
        if custom_instructions:
            msg += f"\n用户的定制指令：{custom_instructions}\n"
        msg += "\n请使用 read_resume 工具读取简历内容，然后使用 match_resume_to_job 工具分析匹配度，最后生成定制后的简历内容。"
        return msg