"""Tracker API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.business_logic.tracker import tracker_service
from src.presentation.api.ai_errors import raise_ai_internal_error, raise_ai_value_error
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.tracker import (
    ApplicationAdviceResponse,
    ApplicationTracker,
    ApplicationTrackerCreate,
    ApplicationTrackerUpdate,
    TrackerAdviceRecord,
)

router = APIRouter()


@router.post("/applications/", response_model=ApplicationTracker)
async def create_application(
    application_data: ApplicationTrackerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await tracker_service.create_application(db, application_data, current_user.id)
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"resume not found": "Resume not found"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create application failed",
        ) from exc


@router.get("/applications/{application_id}", response_model=ApplicationTracker)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    application = await tracker_service.get_application(db, application_id, current_user.id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return application


@router.put("/applications/{application_id}", response_model=ApplicationTracker)
async def update_application(
    application_id: int,
    application_data: ApplicationTrackerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        application = await tracker_service.update_application(
            db, application_id, application_data, current_user.id
        )
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        return application
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update application failed",
        ) from exc


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        deleted = await tracker_service.delete_application(db, application_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete application failed",
        ) from exc


@router.get("/applications/", response_model=list[ApplicationTracker])
async def list_applications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await tracker_service.get_applications(db, current_user.id)


@router.get("/applications/status/{status}", response_model=list[ApplicationTracker])
async def list_applications_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await tracker_service.get_applications_by_status(db, current_user.id, status)


@router.post("/applications/{application_id}/advice/", response_model=ApplicationAdviceResponse)
async def generate_application_advice(
    application_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        result = await tracker_service.generate_tracker_advice_preview(
            db,
            application_id,
            current_user.id,
        )
        return ApplicationAdviceResponse(
            mode="tracker_advice",
            application_id=application_id,
            summary=result["summary"],
            next_steps=result["next_steps"],
            risks=result["risks"],
            raw_content=result.get("raw_content"),
            provider=result.get("provider"),
            model=result.get("model"),
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"application not found": "Application not found"},
            bad_request={"required context is missing", "resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("Tracker advice failed")


@router.post("/applications/{application_id}/advice/persist/", response_model=TrackerAdviceRecord)
async def persist_application_advice(
    application_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await tracker_service.persist_application_advice(
            db,
            application_id,
            current_user.id,
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"application not found": "Application not found"},
            bad_request={"required context is missing", "resume text is empty"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("Tracker advice persistence failed")


@router.get("/applications/{application_id}/advice-history/", response_model=list[TrackerAdviceRecord])
async def list_application_advice_history(
    application_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return await tracker_service.get_tracker_advice_history(
            db,
            application_id,
            current_user.id,
        )
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"application not found": "Application not found"},
        )
    except HTTPException:
        raise
    except Exception:
        raise_ai_internal_error("List tracker advice history failed")
