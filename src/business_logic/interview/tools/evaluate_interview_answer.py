# src/business_logic/interview/tools/evaluate_interview_answer.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class EvaluateInterviewAnswerInput(BaseModel):
    """Input schema for evaluate_interview_answer tool."""
    question: str
    answer: str
    category: str = "技术"


class EvaluateInterviewAnswerTool(BaseTool):
    """评估面试答案质量"""

    name: str = "evaluate_interview_answer"
    description: str = "评估面试答案的质量，给出技术深度、逻辑性、完整性的评分"
    args_schema: Type[BaseModel] = EvaluateInterviewAnswerInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        question = tool_input.get("question", "")
        answer = tool_input.get("answer", "")
        category = tool_input.get("category", "技术")

        if not question or not answer:
            return {"error": "question and answer are required"}

        score = 0
        suggestions = []

        if len(answer) < 20:
            score += 2
            suggestions.append("答案过于简短，建议展开说明")
        elif len(answer) > 50:
            score += 3

        star_keywords = ["项目", "任务", "行动", "结果", "负责", "完成", "实现"]
        if any(kw in answer for kw in star_keywords):
            score += 3
        else:
            suggestions.append("建议使用 STAR 法则组织答案")

        if category == "技术":
            if any(word in answer for word in ["架构", "设计", "优化", "性能"]):
                score += 2
            if any(word in answer for word in ["使用", "采用", "通过"]):
                score += 2

        score = min(10, max(0, score))

        rating = "优秀" if score >= 8 else "良好" if score >= 6 else "一般" if score >= 4 else "需改进"

        return {
            "question": question,
            "category": category,
            "score": score,
            "rating": rating,
            "suggestions": suggestions if suggestions else ["答案基本完整"],
        }