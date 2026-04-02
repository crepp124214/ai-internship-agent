"""
Resume repository helpers.
"""

from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from src.data_access.entities.resume import Resume
from src.data_access.repositories.base_repository import create_repository

_resume_repository = create_repository(Resume)
_base_create = _resume_repository.create
_base_get_by_id = _resume_repository.get_by_id
_base_get_all = _resume_repository.get_all
_base_update = _resume_repository.update
_base_delete = _resume_repository.delete


def create(db: Session, data: dict[str, Any]) -> Resume:
    payload = dict(data)
    original_file_path = payload.get("original_file_path") or payload.get("file_path") or ""
    if not payload.get("file_name"):
        payload["file_name"] = (
            Path(original_file_path).name
            or original_file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            or "unknown"
        )
    if not payload.get("file_type"):
        payload["file_type"] = Path(original_file_path).suffix.lower().lstrip(".") or "unknown"
    return _base_create(db, payload)


def get_by_id(db: Session, resume_id: int) -> Optional[Resume]:
    return _base_get_by_id(db, resume_id)


def get_all(db: Session, order_by: Optional[str] = None) -> List[Resume]:
    return _base_get_all(db, order_by)


def update(db: Session, resume_id: int, data: dict[str, Any]) -> Optional[Resume]:
    return _base_update(db, resume_id, data)


def delete(db: Session, resume_id: int) -> bool:
    return _base_delete(db, resume_id)


def get_by_id_and_user_id(db: Session, resume_id: int, user_id: int) -> Optional[Resume]:
    return (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == user_id)
        .first()
    )


def get_all_by_user_id(db: Session, user_id: int) -> List[Resume]:
    return (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .all()
    )


def update_by_id_and_user_id(
    db: Session,
    resume_id: int,
    user_id: int,
    data: dict[str, Any],
) -> Optional[Resume]:
    resume = get_by_id_and_user_id(db, resume_id, user_id)
    if not resume:
        return None

    for key, value in data.items():
        if hasattr(resume, key):
            setattr(resume, key, value)

    db.commit()
    db.refresh(resume)
    return resume


def delete_by_id_and_user_id(db: Session, resume_id: int, user_id: int) -> bool:
    resume = get_by_id_and_user_id(db, resume_id, user_id)
    if not resume:
        return False

    db.delete(resume)
    db.commit()
    return True


resume_repository = _resume_repository
resume_repository.create = create
resume_repository.get_by_id = get_by_id
resume_repository.get_all = get_all
resume_repository.update = update
resume_repository.delete = delete
