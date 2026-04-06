from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool


class ReadResumeInput(BaseModel):
    """Input schema for read_resume tool."""

    resume_id: int


class ReadResumeTool(BaseTool):
    """读取简历的完整内容"""

    name: str = "read_resume"
    description: str = "读取简历的完整内容，返回简历文本和基本信息"
    args_schema: Type[BaseModel] = ReadResumeInput

    def _execute(self, resume_id: int, runtime=None) -> dict:
        from src.data_access.repositories import resume_repository
        from src.presentation.api.deps import get_db

        db = next(get_db())
        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found", "resume_id": resume_id}

        resume_text = resume.processed_content or resume.resume_text or ""
        return {
            "resume_id": resume_id,
            "resume_text": resume_text,
            "title": resume.title,
        }