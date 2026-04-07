from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class CompareResumesInput(BaseModel):
    """Input schema for compare_resumes tool."""
    resume_id_1: int
    resume_id_2: int


class CompareResumesTool(BaseTool):
    """对比两个简历版本的差异"""

    name: str = "compare_resumes"
    description: str = "对比两个简历版本的差异，输出新增、删除和修改的内容"
    args_schema: Type[BaseModel] = CompareResumesInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id_1 = tool_input.get("resume_id_1")
        resume_id_2 = tool_input.get("resume_id_2")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume1 = resume_repository.get_by_id(db, resume_id_1)
        if not resume1:
            return {"error": f"Resume {resume_id_1} not found"}

        resume2 = resume_repository.get_by_id(db, resume_id_2)
        if not resume2:
            return {"error": f"Resume {resume_id_2} not found"}

        text1 = resume1.processed_content or resume1.resume_text or ""
        text2 = resume2.processed_content or resume2.resume_text or ""

        lines1 = set(text1.split("\n"))
        lines2 = set(text2.split("\n"))

        added = lines2 - lines1
        removed = lines1 - lines2
        common = lines1 & lines2

        return {
            "resume_id_1": resume_id_1,
            "resume_id_2": resume_id_2,
            "added_count": len(added),
            "removed_count": len(removed),
            "common_count": len(common),
            "added_lines": list(added)[:10],
            "removed_lines": list(removed)[:10],
        }
