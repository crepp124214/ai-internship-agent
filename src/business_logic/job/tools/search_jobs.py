from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class SearchJobsInput(BaseModel):
    """Input schema for search_jobs tool."""
    keyword: str
    limit: int = 10


class SearchJobsTool(BaseTool):
    """根据关键词搜索岗位"""

    name: str = "search_jobs"
    description: str = "根据关键词搜索岗位，返回匹配的岗位列表"
    args_schema: Type[BaseModel] = SearchJobsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import job_repository

        keyword = tool_input.get("keyword", "")
        limit = tool_input.get("limit", 10)

        if context is None:
            raise ValueError("ToolContext is required to execute this tool")
        db = context.db

        jobs = job_repository.get_all(db)

        keyword_lower = keyword.lower()
        matched_jobs = [
            {
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": getattr(job, 'location', None),
                "description": (job.description or "")[:200],
            }
            for job in jobs
            if keyword_lower in (job.title or "").lower()
            or keyword_lower in (job.description or "").lower()
            or keyword_lower in (job.company or "").lower()
        ][:limit]

        return {
            "keyword": keyword,
            "count": len(matched_jobs),
            "jobs": matched_jobs,
        }