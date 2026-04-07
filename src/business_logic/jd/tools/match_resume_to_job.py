# src/business_logic/jd/tools/match_resume_to_job.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class MatchResumeToJobInput(BaseModel):
    """Input schema for match_resume_to_job tool."""
    resume_id: int
    jd_id: int


class MatchResumeToJobTool(BaseTool):
    """分析简历与目标岗位的匹配度"""

    name: str = "match_resume_to_job"
    description: str = "输入简历 ID 和岗位 JD ID，返回简历与 JD 的匹配度分析报告"
    args_schema: Type[BaseModel] = MatchResumeToJobInput

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
            raise ValueError("ToolContext is required to execute match_resume_to_job tool")
        db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}
        resume_text = resume.processed_content or resume.resume_text or ""

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        jd_text = job.description or ""
        parser = JdParserService()
        parsed_jd = parser.parse(jd_text)

        matcher = ResumeMatchService()
        report = matcher.compute_match(resume_text, parsed_jd)

        return {
            "resume_id": resume_id,
            "jd_id": jd_id,
            "keyword_coverage": report.keyword_coverage,
            "match_score": report.match_score,
            "gaps": report.gaps,
            "suggestions": report.suggestions,
        }
