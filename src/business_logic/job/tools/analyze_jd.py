from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class AnalyzeJDInput(BaseModel):
    """Input schema for analyze_jd tool."""
    jd_id: int


class AnalyzeJDTool(BaseTool):
    """深度解析 JD（技能要求、薪资范围、经验要求）"""

    name: str = "analyze_jd"
    description: str = "深度解析岗位 JD，提取关键信息（技能要求、经验、薪资等）"
    args_schema: Type[BaseModel] = AnalyzeJDInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import job_repository

        jd_id = tool_input.get("jd_id")

        if context is None:
            raise ValueError("ToolContext is required to execute this tool")
        db = context.db

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        jd_text = job.description or ""

        analysis = {
            "jd_id": jd_id,
            "title": job.title,
            "company": job.company,
        }

        skill_keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust",
            "React", "Vue", "Angular", "Django", "FastAPI", "Spring",
            "MySQL", "PostgreSQL", "MongoDB", "Redis",
            "AWS", "Azure", "Docker", "Kubernetes",
        ]

        found_skills = [s for s in skill_keywords if s.lower() in jd_text.lower()]
        if found_skills:
            analysis["required_skills"] = found_skills

        import re
        exp_patterns = [
            r"(\d+)\+?\s*年",
            r"(\d+)\+?\s*years",
            r"经验\s*(\d+)\s*年",
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                analysis["experience_required"] = f"{match.group(1)} 年"
                break

        edu_keywords = ["本科", "硕士", "博士", "大专", "Bachelor", "Master", "PhD"]
        for edu in edu_keywords:
            if edu.lower() in jd_text.lower():
                analysis["education"] = edu
                break

        analysis["raw_text_length"] = len(jd_text)

        return analysis