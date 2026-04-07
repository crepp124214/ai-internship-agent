from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class GenerateInterviewQuestionsInput(BaseModel):
    """Input schema for generate_interview_questions tool."""
    jd_id: int
    resume_id: int
    count: int = 5


class GenerateInterviewQuestionsTool(BaseTool):
    """根据 JD 和简历生成面试题"""

    name: str = "generate_interview_questions"
    description: str = "根据岗位 JD 和简历生成针对性的面试题"
    args_schema: Type[BaseModel] = GenerateInterviewQuestionsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import job_repository, resume_repository

        jd_id = tool_input.get("jd_id")
        resume_id = tool_input.get("resume_id")
        count = tool_input.get("count", 5)

        if context is None:
            raise ValueError("ToolContext is required to execute this tool")
        db = context.db

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        jd_text = job.description or ""
        resume_text = resume.processed_content or resume.resume_text or ""

        questions = []

        if "python" in jd_text.lower() or "Python" in jd_text:
            questions.append({
                "category": "技术",
                "question": "请描述你在 Python 项目中使用过的主要框架和库",
                "difficulty": "中等",
            })
        if "sql" in jd_text.lower() or "数据库" in jd_text:
            questions.append({
                "category": "技术",
                "question": "你有哪些 SQL 查询优化的经验？",
                "difficulty": "中等",
            })
        if "javascript" in jd_text.lower() or "JS" in jd_text:
            questions.append({
                "category": "技术",
                "question": "请介绍一下你熟悉的 JavaScript 框架",
                "difficulty": "基础",
            })

        questions.append({
            "category": "行为",
            "question": "请描述一个你解决过的最有挑战性的技术问题",
            "difficulty": "中等",
        })

        questions.append({
            "category": "通用",
            "question": "你为什么对这个岗位感兴趣？",
            "difficulty": "基础",
        })

        return {
            "jd_id": jd_id,
            "resume_id": resume_id,
            "count": len(questions),
            "questions": questions[:count],
        }
