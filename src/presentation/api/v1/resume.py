"""
Resume management API.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.presentation.api.ai_errors import raise_ai_internal_error, raise_ai_value_error
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.resume import (
    Resume,
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    ResumeCreate,
    ResumeOptimization,
    ResumeUpdate,
)
from src.business_logic.resume import resume_service
from unittest.mock import MagicMock
from src.presentation.schemas.jd import (
    ResumeCustomizeRequest,
    ResumeCustomizeResponse,
    MatchReportSchema,
)
from src.business_logic.jd import (
    JdParserService,
    ResumeMatchService,
    ResumeCustomizerAgent,
)
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry
from src.business_logic.jd.tools import ReadResumeTool, MatchResumeToJobTool

router = APIRouter()


@router.post("/", response_model=Resume)
async def create_resume(
    resume_data: ResumeCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await resume_service.create_resume(db, current_user, resume_data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create resume failed",
        )


@router.get("/{resume_id}", response_model=Resume)
async def get_resume(
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = await resume_service.get_resume(db, current_user, resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return resume


@router.put("/{resume_id}", response_model=Resume)
async def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        resume = await resume_service.update_resume(
            db,
            current_user,
            resume_id,
            resume_data,
        )
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )
        return resume
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update resume failed",
        )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        deleted = await resume_service.delete_resume(db, current_user, resume_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete resume failed",
        )


@router.get("/", response_model=list[Resume])
async def list_resumes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await resume_service.get_resumes(db, current_user)


@router.post("/{resume_id}/summary/", response_model=ResumeAnalysisResponse)
async def generate_resume_summary(
    resume_id: int,
    analysis_request: ResumeAnalysisRequest | None = Body(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = await resume_service.generate_resume_summary_preview(
            db,
            current_user,
            resume_id,
            target_role=(analysis_request.target_role if analysis_request else None),
        )
        return ResumeAnalysisResponse(
            mode="summary",
            resume_id=resume_id,
            target_role=result.get("target_role"),
            content=result["content"],
            raw_content=result.get("raw_content"),
            provider=result.get("provider"),
            model=result.get("model"),
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
            bad_request={"resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("Resume summary failed")


@router.post("/{resume_id}/summary/persist/", response_model=ResumeOptimization)
async def persist_resume_summary(
    resume_id: int,
    analysis_request: ResumeAnalysisRequest | None = Body(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await resume_service.persist_resume_summary(
            db,
            current_user,
            resume_id,
            target_role=(analysis_request.target_role if analysis_request else None),
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
            bad_request={"resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("Resume summary persistence failed")


@router.get("/{resume_id}/summary/history/", response_model=list[ResumeOptimization])
async def list_resume_summary_history(
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await resume_service.get_resume_summary_history(db, current_user, resume_id)
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("List resume summary history failed")


@router.post("/{resume_id}/improvements/", response_model=ResumeAnalysisResponse)
async def generate_resume_improvements(
    resume_id: int,
    analysis_request: ResumeAnalysisRequest | None = Body(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = await resume_service.generate_resume_improvements_preview(
            db,
            current_user,
            resume_id,
            target_role=(analysis_request.target_role if analysis_request else None),
        )
        return ResumeAnalysisResponse(
            mode="improvements",
            resume_id=resume_id,
            target_role=result.get("target_role"),
            content=result["content"],
            raw_content=result.get("raw_content"),
            provider=result.get("provider"),
            model=result.get("model"),
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
            bad_request={"resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("Resume improvements failed")


@router.post("/{resume_id}/improvements/persist/", response_model=ResumeOptimization)
async def persist_resume_improvements(
    resume_id: int,
    analysis_request: ResumeAnalysisRequest | None = Body(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await resume_service.persist_resume_improvements(
            db,
            current_user,
            resume_id,
            target_role=(analysis_request.target_role if analysis_request else None),
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
            bad_request={"resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("Resume persistence failed")


@router.get("/{resume_id}/optimizations/", response_model=list[ResumeOptimization])
async def list_resume_optimizations(
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await resume_service.get_resume_optimization_history(db, current_user, resume_id)
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("List resume optimizations failed")


@router.post("/{resume_id}/customize-for-jd", response_model=ResumeCustomizeResponse)
async def customize_resume_for_jd(
    resume_id: int,
    req: ResumeCustomizeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    为指定简历生成针对目标岗位定制的简历内容。
    - 解析 JD 关键词和要求
    - 计算简历与 JD 的匹配度
    - Agent 生成定制简历
    """
    import uuid
    from src.data_access.repositories import resume_repository, job_repository

    # 1. 验证简历存在且属于当前用户
    resume = resume_repository.get_by_id_and_user_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # 2. 验证 JD 存在
    job = job_repository.get_by_id(db, req.jd_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    # 3. 解析 JD
    jd_text = job.description or ""
    parser = JdParserService()
    parsed_jd = parser.parse(jd_text)

    # 4. 计算匹配度（仅当 enable_match_report）
    match_report = None
    if req.enable_match_report:
        resume_text = resume.processed_content or resume.resume_text or ""
        matcher = ResumeMatchService()
        match = matcher.compute_match(resume_text, parsed_jd)
        match_report = MatchReportSchema(
            keyword_coverage=match.keyword_coverage,
            match_score=match.match_score,
            gaps=match.gaps,
            suggestions=match.suggestions,
        )

    # 5. 构建 Agent
    session_id = str(uuid.uuid4())
    tool_registry = ToolRegistry()
    tool_registry.register(ReadResumeTool())
    tool_registry.register(MatchResumeToJobTool())

    mock_memory = MagicMock()
    mock_memory.search_memory.return_value = []
    mock_memory.get_turns.return_value = []

    llm = LiteLLMAdapter()
    agent = ResumeCustomizerAgent(
        llm=llm,
        tool_registry=tool_registry,
        memory=mock_memory,
    )

    # 6. 执行定制
    customized_text = await agent.customize(
        resume_id=resume_id,
        jd_id=req.jd_id,
        custom_instructions=req.custom_instructions,
        session_id=session_id,
    )

    return ResumeCustomizeResponse(
        customized_resume=customized_text,
        match_report=match_report,
        session_id=session_id,
    )


