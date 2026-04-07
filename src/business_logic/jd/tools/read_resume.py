from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class ReadResumeInput(BaseModel):
    """Input schema for read_resume tool."""
    resume_id: int


class ReadResumeTool(BaseTool):
    """读取简历的完整内容"""

    name: str = "read_resume"
    description: str = "读取简历的完整内容，返回简历文本和基本信息"
    args_schema: Type[BaseModel] = ReadResumeInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")
        if context is None:
            raise ValueError("ToolContext is required to execute read_resume tool")
        db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found", "resume_id": resume_id}

        resume_text = resume.processed_content or resume.resume_text or ""
        return {
            "resume_id": resume_id,
            "resume_text": resume_text,
            "title": resume.title,
        }
