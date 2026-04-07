from typing import Optional, Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class UpdateResumeInput(BaseModel):
    """Input schema for update_resume tool."""
    resume_id: int
    title: Optional[str] = None
    resume_text: Optional[str] = None
    processed_content: Optional[str] = None


class UpdateResumeTool(BaseTool):
    """更新简历内容（标题、文本、处理后的内容）"""

    name: str = "update_resume"
    description: str = "更新简历的标题或内容，支持部分更新"
    args_schema: Type[BaseModel] = UpdateResumeInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")
        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        if "title" in tool_input and tool_input["title"] is not None:
            resume.title = tool_input["title"]
        if "resume_text" in tool_input and tool_input["resume_text"] is not None:
            resume.resume_text = tool_input["resume_text"]
        if "processed_content" in tool_input and tool_input["processed_content"] is not None:
            resume.processed_content = tool_input["processed_content"]

        db.commit()
        db.refresh(resume)

        return {
            "resume_id": resume_id,
            "updated": True,
            "title": resume.title,
        }