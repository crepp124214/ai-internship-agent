from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class WebSearchInput(BaseModel):
    """Input schema for web_search tool."""
    query: str
    limit: int = 5


class WebSearchTool(BaseTool):
    """网络搜索（公司信息、行业动态等）"""

    name: str = "web_search"
    description: str = "搜索互联网获取公司信息、行业动态、职位信息等"
    args_schema: Type[BaseModel] = WebSearchInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from urllib.parse import quote

        query = tool_input.get("query", "")
        limit = tool_input.get("limit", 5)

        if not query:
            return {"error": "query is required"}

        encoded_query = quote(query)

        return {
            "query": query,
            "limit": limit,
            "results": [
                {
                    "title": f"{query} - 相关结果 1",
                    "url": f"https://example.com/result1?q={encoded_query}",
                    "snippet": f"关于 {query} 的搜索结果示例...",
                },
                {
                    "title": f"{query} - 相关结果 2",
                    "url": f"https://example.com/result2?q={encoded_query}",
                    "snippet": f"更多关于 {query} 的信息...",
                },
            ][:limit],
            "note": "实际生产环境应使用付费搜索 API（如 SerpAPI）",
        }
