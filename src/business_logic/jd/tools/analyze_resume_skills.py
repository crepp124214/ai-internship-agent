from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class AnalyzeResumeSkillsInput(BaseModel):
    """Input schema for analyze_resume_skills tool."""
    resume_id: int


class AnalyzeResumeSkillsTool(BaseTool):
    """提取并分析简历中的技能标签"""

    name: str = "analyze_resume_skills"
    description: str = "从简历中提取技能标签，并按类别分组分析"
    args_schema: Type[BaseModel] = AnalyzeResumeSkillsInput

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
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        resume_text = resume.processed_content or resume.resume_text or ""

        skill_keywords = {
            "编程语言": ["Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#"],
            "框架": ["React", "Vue", "Angular", "Django", "FastAPI", "Spring", "Node.js"],
            "数据库": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
            "云服务": ["AWS", "Azure", "GCP", "Docker", "Kubernetes"],
            "AI/ML": ["TensorFlow", "PyTorch", "LangChain", "OpenAI", "HuggingFace"],
        }

        found_skills = {}
        text_upper = resume_text.upper()

        for category, keywords in skill_keywords.items():
            matched = [kw for kw in keywords if kw.upper() in text_upper]
            if matched:
                found_skills[category] = matched

        return {
            "resume_id": resume_id,
            "skills": found_skills,
            "total_count": sum(len(v) for v in found_skills.values()),
        }