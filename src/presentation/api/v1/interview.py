"""Interview management API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.business_logic.interview import interview_service
from src.presentation.api.ai_errors import raise_ai_internal_error, raise_ai_value_error
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.interview import (
    CoachStartRequest, CoachStartResponse,
    CoachAnswerRequest, CoachAnswerResponse,
    CoachEndResponse, ReviewReportResponse,
    InterviewRecordEvaluationRequest,
    InterviewRecordEvaluationResponse,
    InterviewAnswerEvaluationRequest,
    InterviewAnswerEvaluationResponse,
    InterviewQuestion,
    InterviewQuestionCreate,
    InterviewQuestionGenerationRequest,
    InterviewQuestionGenerationResponse,
    InterviewQuestionUpdate,
    InterviewRecord,
    InterviewRecordCreate,
    InterviewSession,
    InterviewSessionCreate,
)
from src.business_logic.interview.coach_service import coach_service

router = APIRouter()


@router.post("/questions/", response_model=InterviewQuestion)
async def create_question(
    question_data: InterviewQuestionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await interview_service.create_question(db, question_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create interview question failed",
        )


@router.get("/questions/{question_id}", response_model=InterviewQuestion)
async def get_question(
    question_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = await interview_service.get_question(db, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview question not found",
        )
    return question


@router.put("/questions/{question_id}", response_model=InterviewQuestion)
async def update_question(
    question_id: int,
    question_data: InterviewQuestionUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        question = await interview_service.update_question(db, question_id, question_data)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview question not found",
            )
        return question
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update interview question failed",
        )


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        deleted = await interview_service.delete_question(db, question_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview question not found",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete interview question failed",
        )


@router.get("/questions/", response_model=list[InterviewQuestion])
async def list_questions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await interview_service.get_questions(db)


@router.get("/questions/category/{category}", response_model=list[InterviewQuestion])
async def list_questions_by_category(
    category: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await interview_service.get_questions_by_category(db, category)


@router.get("/questions/random/", response_model=list[InterviewQuestion])
async def get_random_questions(
    count: int = 5,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await interview_service.get_random_questions(db, count)


@router.post("/questions/generate/", response_model=InterviewQuestionGenerationResponse)
async def generate_questions(
    request: InterviewQuestionGenerationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await interview_service.generate_interview_questions_preview(
            db,
            current_user.id,
            job_context=request.job_context,
            resume_id=request.resume_id,
            count=request.count,
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "resume not found"},
        )
    except Exception:
        raise_ai_internal_error("Generate interview questions failed")


@router.post("/answers/evaluate/", response_model=InterviewAnswerEvaluationResponse)
async def evaluate_answer(
    request: InterviewAnswerEvaluationRequest,
    current_user=Depends(get_current_user),
):
    try:
        return await interview_service.evaluate_interview_answer_preview(
            question_text=request.question_text,
            user_answer=request.user_answer,
            job_context=request.job_context,
        )
    except ValueError as exc:
        raise_ai_value_error(str(exc), not_found={})
    except Exception:
        raise_ai_internal_error("Evaluate interview answer failed")


@router.post("/sessions/", response_model=InterviewSession)
async def create_session(
    session_data: InterviewSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await interview_service.create_session(db, session_data, current_user.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create interview session failed",
        ) from exc


@router.get("/sessions/", response_model=list[InterviewSession])
async def list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await interview_service.get_sessions(db, current_user.id)


@router.post("/records/", response_model=InterviewRecord)
async def create_record(
    record_data: InterviewRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await interview_service.create_record(db, record_data, current_user.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create interview record failed",
        ) from exc


@router.get("/records/", response_model=list[InterviewRecord])
async def list_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await interview_service.get_records(db, current_user.id)


@router.post("/records/{record_id}/evaluate/", response_model=InterviewRecordEvaluationResponse)
async def evaluate_record(
    record_id: int,
    request: InterviewRecordEvaluationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        result = await interview_service.persist_interview_record_evaluation(
            db,
            record_id=record_id,
            current_user_id=current_user.id,
            job_context=request.job_context,
        )
        if isinstance(result, dict):
            result.setdefault("mode", "answer_evaluation")
            result.setdefault("raw_content", result.get("ai_evaluation", ""))
            return result
        return {
            "mode": "answer_evaluation",
            "record_id": result.id,
            "score": result.score,
            "feedback": result.feedback or "",
            "ai_evaluation": result.ai_evaluation or "",
            "raw_content": result.ai_evaluation or "",
            "provider": getattr(result, "provider", None),
            "model": getattr(result, "model", None),
            "answered_at": result.answered_at,
        }
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={
                "interview record not found": "interview record not found",
                "interview question not found": "interview question not found",
            },
        )
    except Exception:
        raise_ai_internal_error("Evaluate interview record failed")


@router.post("/coach/start", response_model=CoachStartResponse)
async def coach_start(
    req: CoachStartRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """启动 AI 面试对练会话"""
    try:
        result = coach_service.start_session(
            db=db,
            user=current_user,
            jd_id=req.jd_id,
            resume_id=req.resume_id,
            question_count=req.question_count,
        )
        return CoachStartResponse(**result)
    except ValueError as exc:
        from fastapi import HTTPException
        msg = str(exc)
        if "not found" in msg.lower() or "不存在" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)


@router.post("/coach/answer", response_model=CoachAnswerResponse)
async def coach_answer(
    req: CoachAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交回答，获取评分和下一题"""
    try:
        result = coach_service.submit_answer(
            db=db,
            user=current_user,
            session_id=req.session_id,
            answer=req.answer,
        )
        return CoachAnswerResponse(**result)
    except ValueError as exc:
        from fastapi import HTTPException
        msg = str(exc)
        if "已结束" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=404, detail=msg)


@router.post("/coach/followup", response_model=CoachEndResponse)
async def coach_followup(
    req: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交追问轮回答，获取复盘报告"""
    try:
        result = coach_service.submit_followup_answers(
            db=db,
            user=current_user,
            session_id=req["session_id"],
            followup_answers=req.get("followup_answers", []),
        )
        return CoachEndResponse(**result)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/coach/end", response_model=CoachEndResponse)
async def coach_end(
    session_id: int,
    followup_skipped: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提前结束面试，获取复盘报告"""
    try:
        result = coach_service.end_session(
            db=db,
            user=current_user,
            session_id=session_id,
            followup_skipped=followup_skipped,
        )
        return CoachEndResponse(**result)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/coach/report/{session_id}", response_model=ReviewReportResponse)
async def coach_get_report(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取历史复盘报告"""
    from src.data_access.entities.interview import InterviewSession
    from src.data_access.repositories.interview_repository import interview_session_repository

    session = interview_session_repository.get_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session not completed yet")

    records = session.interview_records.all()
    answers = [
        {"question": r.user_answer or "", "answer": r.user_answer or "", "score": r.score or 0}
        for r in records
    ]
    gen = ReviewReportGenerator()
    report = gen.generate(answers)

    return ReviewReportResponse(
        session_id=session_id,
        review_report=report,
        average_score=session.average_score or 0,
    )
