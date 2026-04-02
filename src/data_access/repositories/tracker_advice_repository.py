"""Tracker advice repository helpers."""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.data_access.entities.job import JobApplication
from src.data_access.entities.tracker import TrackerAdvice
from src.data_access.repositories.base_repository import create_repository

_tracker_advice_repository = create_repository(TrackerAdvice)
_base_create = _tracker_advice_repository.create
_base_get_by_id = _tracker_advice_repository.get_by_id
_base_update = _tracker_advice_repository.update
_base_delete = _tracker_advice_repository.delete


def create(db: Session, data: dict) -> TrackerAdvice:
    return _base_create(db, data)


def get_by_id(db: Session, advice_id: int) -> Optional[TrackerAdvice]:
    return _base_get_by_id(db, advice_id)


def update(db: Session, advice_id: int, data: dict) -> Optional[TrackerAdvice]:
    return _base_update(db, advice_id, data)


def delete(db: Session, advice_id: int) -> bool:
    return _base_delete(db, advice_id)


def get_by_id_and_user_id(
    db: Session,
    advice_id: int,
    user_id: int,
) -> Optional[TrackerAdvice]:
    return (
        db.query(TrackerAdvice)
        .join(JobApplication)
        .filter(
            TrackerAdvice.id == advice_id,
            JobApplication.user_id == user_id,
        )
        .first()
    )


def get_all_by_application_id_and_user_id(
    db: Session,
    application_id: int,
    user_id: int,
) -> List[TrackerAdvice]:
    return (
        db.query(TrackerAdvice)
        .join(JobApplication)
        .filter(
            TrackerAdvice.application_id == application_id,
            JobApplication.user_id == user_id,
        )
        .order_by(TrackerAdvice.created_at.desc(), TrackerAdvice.id.desc())
        .all()
    )


tracker_advice_repository = _tracker_advice_repository
tracker_advice_repository.create = create
tracker_advice_repository.get_by_id = get_by_id
tracker_advice_repository.update = update
tracker_advice_repository.delete = delete
tracker_advice_repository.get_by_id_and_user_id = get_by_id_and_user_id
tracker_advice_repository.get_all_by_application_id_and_user_id = get_all_by_application_id_and_user_id
