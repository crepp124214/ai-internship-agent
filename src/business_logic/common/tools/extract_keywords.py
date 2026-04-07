# src/business_logic/common/tools/extract_keywords.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class ExtractKeywordsInput(BaseModel):
    """Input schema for extract_keywords tool."""
    text: str
    limit: int = 10


class ExtractKeywordsTool(BaseTool):
    """从文本中提取关键词"""

    name: str = "extract_keywords"
    description: str = "从文本中提取关键词，用于简历优化、JD 分析等场景"
    args_schema: Type[BaseModel] = ExtractKeywordsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        import re

        text = tool_input.get("text", "")
        limit = tool_input.get("limit", 10)

        if not text:
            return {"error": "text is required"}

        stop_words = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
        }

        words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

        filtered = [w for w in words if w not in stop_words and len(w) > 1]

        freq = {}
        for word in filtered:
            freq[word] = freq.get(word, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [{"word": w, "count": c} for w, c in sorted_words[:limit]]

        return {
            "text_length": len(text),
            "keyword_count": len(keywords),
            "keywords": keywords,
        }