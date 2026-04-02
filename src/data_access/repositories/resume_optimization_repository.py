"""Resume optimization repository helpers."""

from typing import Any, List, Optional

from sqlalchemy.orm import Session

from src.data_access.entities.resume import Resume, ResumeOptimization
from src.data_access.repositories.base_repository import create_repository

_resume_optimization_repository = create_repository(ResumeOptimization)
_base_create = _resume_optimization_repository.create
_base_get_by_id = _resume_optimization_repository.get_by_id
_base_get_all = _resume_optimization_repository.get_all
_base_update = _resume_optimization_repository.update
_base_delete = _resume_optimization_repository.delete


def create(db: Session, data: dict[str, Any]) -> ResumeOptimization:
    return _base_create(db, data)


def get_by_id(db: Session, optimization_id: int) -> Optional[ResumeOptimization]:
    return _base_get_by_id(db, optimization_id)


def get_all(
    db: Session,
    order_by: Optional[str] = "created_at",
) -> List[ResumeOptimization]:
    return _base_get_all(db, order_by)


def update(
    db: Session,
    optimization_id: int,
    data: dict[str, Any],
) -> Optional[ResumeOptimization]:
    return _base_update(db, optimization_id, data)


def delete(db: Session, optimization_id: int) -> bool:
    return _base_delete(db, optimization_id)


def get_by_id_and_user_id(
    db: Session,
    optimization_id: int,
    user_id: int,
) -> Optional[ResumeOptimization]:
    return (
        db.query(ResumeOptimization)
        .join(Resume)
        .filter(
            ResumeOptimization.id == optimization_id,
            Resume.user_id == user_id,
        )
        .first()
    )


def get_all_by_resume_id_and_user_id(
    db: Session,
    resume_id: int,
    user_id: int,
) -> List[ResumeOptimization]:
    return (
        db.query(ResumeOptimization)
        .join(Resume)
        .filter(
            ResumeOptimization.resume_id == resume_id,
            Resume.user_id == user_id,
        )
        .order_by(ResumeOptimization.created_at.desc(), ResumeOptimization.id.desc())
        .all()
    )


def get_all_by_resume_id(
    db: Session,
    resume_id: int,
    user_id: int | None = None,
) -> List[ResumeOptimization]:
    query = db.query(ResumeOptimization).filter(ResumeOptimization.resume_id == resume_id)
    if user_id is not None:
        query = query.join(Resume).filter(Resume.user_id == user_id)
    return query.order_by(ResumeOptimization.created_at.desc(), ResumeOptimization.id.desc()).all()


def get_all_by_resume_id_and_mode(
    db: Session,
    resume_id: int,
    mode: str,
    user_id: int | None = None,
) -> List[ResumeOptimization]:
    query = db.query(ResumeOptimization).filter(
        ResumeOptimization.resume_id == resume_id,
        ResumeOptimization.mode == mode,
    )
    if user_id is not None:
        query = query.join(Resume).filter(Resume.user_id == user_id)
    return query.order_by(ResumeOptimization.created_at.desc(), ResumeOptimization.id.desc()).all()


resume_optimization_repository = _resume_optimization_repository
resume_optimization_repository.create = create
resume_optimization_repository.get_by_id = get_by_id
resume_optimization_repository.get_all = get_all
resume_optimization_repository.update = update
resume_optimization_repository.delete = delete
resume_optimization_repository.get_by_id_and_user_id = get_by_id_and_user_id
resume_optimization_repository.get_all_by_resume_id_and_user_id = get_all_by_resume_id_and_user_id
resume_optimization_repository.get_all_by_resume_id = get_all_by_resume_id
resume_optimization_repository.get_all_by_resume_id_and_mode = get_all_by_resume_id_and_mode
