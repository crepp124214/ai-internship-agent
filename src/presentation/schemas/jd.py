# src/presentation/schemas/jd.py
"""JD-customized resume API schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ResumeCustomizeRequest(BaseModel):
    """Request to customize a resume for a specific job."""

    jd_id: int = Field(..., ge=1, description="目标岗位 ID")
    custom_instructions: Optional[str] = Field(
        default=None, description="用户可选的定制指令"
    )
    enable_match_report: bool = Field(
        default=True, description="是否输出匹配报告"
    )


class MatchReportSchema(BaseModel):
    """Match report embedded in response."""

    keyword_coverage: dict[str, bool] = Field(
        ..., description="关键词 → 是否覆盖"
    )
    match_score: float = Field(..., ge=0.0, le=1.0, description="0.0 ~ 1.0 匹配度")
    gaps: list[str] = Field(default_factory=list, description="未覆盖的关键要求")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")


class ResumeCustomizeResponse(BaseModel):
    """Response for resume customization."""

    customized_resume: str = Field(..., description="定制后的简历内容（纯文本 Markdown）")
    match_report: Optional[MatchReportSchema] = Field(
        default=None, description="匹配报告"
    )
    session_id: str = Field(..., description="本次 Agent 执行 session_id")
