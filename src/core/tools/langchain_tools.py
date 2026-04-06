"""
LangChain @tool 装饰器辅助函数
提供从 @tool 装饰器函数转换为 BaseTool 的能力
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Type

from langchain_core.tools import convert_to_openai_tool

from src.core.tools.base_tool import BaseTool


def langchain_tool_to_basetool(
    langchain_tool: Any,
) -> BaseTool:
    """
    将 LangChain @tool 装饰器创建的工具转换为我们的 BaseTool
    """

    class WrappedBaseTool(BaseTool):
        name: str = langchain_tool.name
        description: str = langchain_tool.description

        def _execute_sync(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
            result = langchain_tool.invoke(tool_input, config={"tool_call": True})
            if isinstance(result, str):
                return {"result": result}
            return result if isinstance(result, dict) else {"result": result}

    return WrappedBaseTool()


def get_openai_tool_schemas(tools: list[BaseTool]) -> list[Dict[str, Any]]:
    """
    从 BaseTool 列表生成 OpenAI function calling 格式的 schemas
    """
    return [convert_to_openai_tool(tool) for tool in tools]