from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class FormatResumeInput(BaseModel):
    """Input schema for format_resume tool."""
    resume_id: int


class FormatResumeTool(BaseTool):
    """格式化简历（Markdown → 结构化输出）"""

    name: str = "format_resume"
    description: str = "将简历内容格式化为结构化输出"
    args_schema: Type[BaseModel] = FormatResumeInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")

        if context is None:
            raise ValueError("ToolContext is required to execute this tool")
        db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        resume_text = resume.processed_content or resume.resume_text or ""

        lines = resume_text.split("\n")
        sections = {}
        current_section = "个人信息"
        current_content = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = stripped.lstrip("#").strip()
                current_content = []
            elif stripped.startswith("-"):
                current_content.append(stripped)
            else:
                current_content.append(stripped)

        if current_content:
            sections[current_section] = "\n".join(current_content)

        return {
            "resume_id": resume_id,
            "title": resume.title,
            "sections": sections,
            "section_count": len(sections),
        }
