"""Job match result repository helpers."""

from typing import Any, List, Optional

from sqlalchemy.orm import Session

from src.data_access.entities.job import Job, JobMatchResult
from src.data_access.entities.resume import Resume
from src.data_access.repositories.base_repository import create_repository

_job_match_result_repository = create_repository(JobMatchResult)
_base_create = _job_match_result_repository.create
_base_get_by_id = _job_match_result_repository.get_by_id
_base_get_all = _job_match_result_repository.get_all
_base_update = _job_match_result_repository.update
_base_delete = _job_match_result_repository.delete


def create(db: Session, data: dict[str, Any]) -> JobMatchResult:
    return _base_create(db, data)


def get_by_id(db: Session, result_id: int) -> Optional[JobMatchResult]:
    return _base_get_by_id(db, result_id)


def get_all(
    db: Session,
    order_by: Optional[str] = "created_at",
) -> List[JobMatchResult]:
    return _base_get_all(db, order_by)


def update(
    db: Session,
    result_id: int,
    data: dict[str, Any],
) -> Optional[JobMatchResult]:
    return _base_update(db, result_id, data)


def delete(db: Session, result_id: int) -> bool:
    return _base_delete(db, result_id)


def get_by_id_and_user_id(
    db: Session,
    result_id: int,
    user_id: int,
) -> Optional[JobMatchResult]:
    return (
        db.query(JobMatchResult)
        .join(Resume)
        .filter(JobMatchResult.id == result_id, Resume.user_id == user_id)
        .first()
    )


def get_all_by_job_id_and_user_id(
    db: Session,
    job_id: int,
    user_id: int,
) -> List[JobMatchResult]:
    return (
        db.query(JobMatchResult)
        .join(Resume)
        .filter(JobMatchResult.job_id == job_id, Resume.user_id == user_id)
        .order_by(JobMatchResult.created_at.desc(), JobMatchResult.id.desc())
        .all()
    )


job_match_result_repository = _job_match_result_repository
job_match_result_repository.create = create
job_match_result_repository.get_by_id = get_by_id
job_match_result_repository.get_all = get_all
job_match_result_repository.update = update
job_match_result_repository.delete = delete
job_match_result_repository.get_by_id_and_user_id = get_by_id_and_user_id
job_match_result_repository.get_all_by_job_id_and_user_id = get_all_by_job_id_and_user_id
