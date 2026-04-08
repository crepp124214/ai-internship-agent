"""助手服务 — Agent 助手面板的后端逻辑"""

from dataclasses import dataclass
from typing import AsyncIterator, Optional

from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.tool_registry import ToolRegistry


@dataclass
class AssistantContext:
    """助手上下文"""
    page: str  # "resume" | "job"
    resource_id: Optional[int] = None
    resource_ids: Optional[list[int]] = None
    history: Optional[list[dict]] = None


class AssistantService:
    """处理 Agent 助手面板的对话请求"""

    _tool_registry_cache: Optional[ToolRegistry] = None

    def __init__(self) -> None:
        self._llm = LiteLLMAdapter()
        self._memory = MemoryStore()
        self._state_machine = StateMachine()
        self._context_builder = ContextBuilder(memory=self._memory)
        self._tool_registry = self._build_tool_registry()

    def _build_tool_registry(self) -> ToolRegistry:
        if AssistantService._tool_registry_cache is not None:
            return AssistantService._tool_registry_cache

        from src.business_logic.jd.tools.read_resume import ReadResumeTool
        from src.business_logic.jd.tools.analyze_resume_skills import AnalyzeResumeSkillsTool
        from src.business_logic.jd.tools.format_resume import FormatResumeTool
        from src.business_logic.job.tools.search_jobs import SearchJobsTool
        from src.business_logic.job.tools.analyze_jd import AnalyzeJDTool
        from src.business_logic.common.tools.web_search import WebSearchTool

        registry = ToolRegistry()
        for tool_cls in [
            ReadResumeTool,
            AnalyzeResumeSkillsTool,
            FormatResumeTool,
            SearchJobsTool,
            AnalyzeJDTool,
            WebSearchTool,
        ]:
            registry.register(tool_cls())
        AssistantService._tool_registry_cache = registry
        return registry

    def build_system_prompt(self, page: str, resource_id: Optional[int] = None) -> str:
        """根据页面上下文构建 System Prompt"""
        page_descriptions = {
            "resume": "用户正在查看简历页面。",
            "job": "用户正在查看岗位页面。",
        }
        base = page_descriptions.get(page, "用户正在使用求职助手。")
        if resource_id:
            base += f" 当前选中的资源 ID：{resource_id}。"
        base += "\n你是求职过程中的智能助手，根据用户请求分析简历或岗位，提供专业建议。"
        return base

    def build_context(
        self,
        page: str,
        resource_id: Optional[int] = None,
        resource_ids: Optional[list[int]] = None,
        history: Optional[list[dict]] = None,
    ) -> dict:
        """构建助手上下文"""
        return {
            "page": page,
            "resource_id": resource_id,
            "resource_ids": resource_ids or [],
            "history": history or [],
        }

    async def chat(
        self,
        message: str,
        context: AssistantContext,
    ) -> AsyncIterator[dict]:
        """
        执行对话，流式返回事件。
        事件类型：step, final, done, error
        """
        system_prompt = self.build_system_prompt(context.page, context.resource_id)
        allowed_pages = {"resume", "job"}
        page = context.page if context.page in allowed_pages else "unknown"
        session_id = f"assistant_{page}_{context.resource_id or 'none'}"

        executor = AgentExecutor(
            llm=self._llm,
            tools=self._tool_registry,
            memory=self._memory,
            state_machine=self._state_machine,
            context_builder=self._context_builder,
        )

        try:
            async for chunk in executor.execute(
                task=message,
                session_id=session_id,
                system_prompt=system_prompt,
            ):
                if chunk:
                    yield {"type": "step", "content": chunk}
            yield {"type": "done", "content": ""}
        except Exception as exc:
            yield {"type": "error", "content": str(exc)}