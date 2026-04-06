"""Job management API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.business_logic.job import job_service
from src.presentation.api.ai_errors import raise_ai_internal_error, raise_ai_value_error
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.job import (
    Job,
    JobApplication,
    JobApplicationCreate,
    JobCreate,
    JobMatchRecord,
    JobMatchRequest,
    JobMatchResponse,
    JobUpdate,
)

router = APIRouter()

TRACKER_APPLICATIONS_DETAIL = "Job applications are managed by /api/v1/tracker/applications/"


def _result_value(result, key: str):
    if isinstance(result, dict):
        return result[key]
    return getattr(result, key)


@router.post("/", response_model=Job)
async def create_job(
    job_data: JobCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        _ = current_user
        return await job_service.create_job(db, job_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create job failed",
        ) from exc


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="岗位不存在",
        )
    return job


@router.put("/{job_id}", response_model=Job)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        _ = current_user
        job = await job_service.update_job(db, job_id, job_data)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="岗位不存在",
            )
        return job
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update job failed",
        ) from exc


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        _ = current_user
        deleted = await job_service.delete_job(db, job_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="岗位不存在",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete job failed",
        ) from exc


@router.get("/", response_model=list[Job])
async def list_jobs(db: Session = Depends(get_db)):
    return await job_service.get_jobs(db)


@router.post("/{job_id}/match/", response_model=JobMatchResponse)
async def match_job_to_resume(
    job_id: int,
    match_request: JobMatchRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = await job_service.generate_job_match_preview(
            db,
            job_id=job_id,
            resume_id=match_request.resume_id,
            current_user_id=current_user.id,
        )
        return JobMatchResponse(
            mode="job_match",
            job_id=job_id,
            resume_id=match_request.resume_id,
            score=_result_value(result, "score"),
            feedback=_result_value(result, "feedback"),
            raw_content=_result_value(result, "raw_content"),
            provider=_result_value(result, "provider"),
            model=_result_value(result, "model"),
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={
                "job not found": "job not found",
                "resume not found": "resume not found",
            },
            bad_request={"resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise_ai_internal_error(f"Job match failed: {exc}")


@router.post("/{job_id}/match/persist/", response_model=JobMatchRecord)
async def persist_job_match(
    job_id: int,
    match_request: JobMatchRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await job_service.persist_job_match(
            db,
            job_id=job_id,
            resume_id=match_request.resume_id,
            current_user_id=current_user.id,
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={
                "job not found": "job not found",
                "resume not found": "resume not found",
            },
            bad_request={"resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise_ai_internal_error(f"Job match persistence failed: {exc}")


@router.get("/{job_id}/match-history/", response_model=list[JobMatchRecord])
async def list_job_match_history(
    job_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await job_service.get_job_match_history(db, job_id, current_user.id)
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"job not found": "job not found"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("List job match history failed")


@router.get("/search/", response_model=list[Job])
async def search_jobs(
    keyword: str = None,
    location: str = None,
    db: Session = Depends(get_db),
):
    return await job_service.search_jobs(db, keyword, location)


@router.post("/applications/", response_model=JobApplication)
async def create_application(
    application_data: JobApplicationCreate,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=TRACKER_APPLICATIONS_DETAIL,
    )


@router.get("/applications/", response_model=list[JobApplication])
async def list_applications(db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=TRACKER_APPLICATIONS_DETAIL,
    )
