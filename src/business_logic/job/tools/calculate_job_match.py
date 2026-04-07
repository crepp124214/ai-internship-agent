from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class CalculateJobMatchInput(BaseModel):
    """Input schema for calculate_job_match tool."""
    resume_id: int
    jd_id: int


class CalculateJobMatchTool(BaseTool):
    """计算简历与岗位的匹配度（数值化）"""

    name: str = "calculate_job_match"
    description: str = "计算简历与岗位的数值化匹配度得分（0-100）"
    args_schema: Type[BaseModel] = CalculateJobMatchInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.business_logic.jd.jd_parser_service import JdParserService
        from src.business_logic.jd.resume_match_service import ResumeMatchService
        from src.data_access.repositories import resume_repository, job_repository

        resume_id = tool_input.get("resume_id")
        jd_id = tool_input.get("jd_id")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        resume_text = resume.processed_content or resume.resume_text or ""
        jd_text = job.description or ""

        parser = JdParserService()
        parsed_jd = parser.parse(jd_text)

        matcher = ResumeMatchService()
        report = matcher.compute_match(resume_text, parsed_jd)

        return {
            "resume_id": resume_id,
            "jd_id": jd_id,
            "match_score": report.match_score,
            "keyword_coverage": report.keyword_coverage,
            "gaps": report.gaps,
            "suggestions": report.suggestions,
        }
