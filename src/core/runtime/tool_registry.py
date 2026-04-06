"""
工具注册表
负责工具的注册、发现、schema 导出
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.core.tools.base_tool import BaseTool


class ToolRegistry:
    """
    全局工具注册表
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError("Tool must have a name")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        return tool

    def list_tools(self) -> List[Dict[str, Any]]:
        """返回所有工具的描述性信息列表"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema.schema() if tool.args_schema else {},
            }
            for tool in self._tools.values()
        ]

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        返回 LangChain / OpenAI function calling 格式的 tool schemas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.args_schema.schema() if tool.args_schema else {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, tool_input: Dict[str, Any], runtime: Any = None) -> Any:
        """执行工具，返回结果"""
        import json
        tool = self.get_tool(name)
        result = tool._run(tool_input, runtime=runtime)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return result
        return result