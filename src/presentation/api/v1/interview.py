"""Interview management API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.business_logic.interview import interview_service
from src.presentation.api.ai_errors import raise_ai_internal_error, raise_ai_value_error
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.interview import (
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

router = APIRouter()


@router.post("/questions/", response_model=InterviewQuestion)
async def create_question(
    question_data: InterviewQuestionCreate,
    db: Session = Depends(get_db),
):
    try:
        return await interview_service.create_question(db, question_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create interview question failed: {exc}",
        ) from exc


@router.get("/questions/{question_id}", response_model=InterviewQuestion)
async def get_question(question_id: int, db: Session = Depends(get_db)):
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update interview question failed: {exc}",
        ) from exc


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    try:
        deleted = await interview_service.delete_question(db, question_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview question not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete interview question failed: {exc}",
        ) from exc


@router.get("/questions/", response_model=list[InterviewQuestion])
async def list_questions(db: Session = Depends(get_db)):
    return await interview_service.get_questions(db)


@router.get("/questions/category/{category}", response_model=list[InterviewQuestion])
async def list_questions_by_category(category: str, db: Session = Depends(get_db)):
    return await interview_service.get_questions_by_category(db, category)


@router.get("/questions/random/", response_model=list[InterviewQuestion])
async def get_random_questions(count: int = 5, db: Session = Depends(get_db)):
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
    except Exception as exc:
        raise_ai_internal_error(f"Generate interview questions failed: {exc}")


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
    except Exception as exc:
        raise_ai_internal_error(f"Evaluate interview answer failed: {exc}")


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
            detail=f"Create interview session failed: {exc}",
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
            detail=f"Create interview record failed: {exc}",
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
    except Exception as exc:
        raise_ai_internal_error(f"Evaluate interview record failed: {exc}")
