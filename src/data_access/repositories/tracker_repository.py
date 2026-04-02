"""Tracker repository helpers."""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.data_access.entities.job import JobApplication
from src.data_access.repositories.base_repository import BaseRepository


class TrackerRepository(BaseRepository[JobApplication]):
    def get_by_user_id(self, db: Session, user_id: int) -> List[JobApplication]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

    def get_by_id_and_user_id(
        self, db: Session, application_id: int, user_id: int
    ) -> Optional[JobApplication]:
        return (
            db.query(self.model)
            .filter(self.model.id == application_id, self.model.user_id == user_id)
            .first()
        )

    def get_by_user_id_and_status(
        self, db: Session, user_id: int, status: str
    ) -> List[JobApplication]:
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.status == status)
            .all()
        )

    def update_by_id_and_user_id(
        self, db: Session, application_id: int, user_id: int, data: dict
    ) -> Optional[JobApplication]:
        instance = self.get_by_id_and_user_id(db, application_id, user_id)
        if not instance:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        db.commit()
        db.refresh(instance)
        return instance

    def delete_by_id_and_user_id(
        self, db: Session, application_id: int, user_id: int
    ) -> bool:
        instance = self.get_by_id_and_user_id(db, application_id, user_id)
        if not instance:
            return False

        db.delete(instance)
        db.commit()
        return True


tracker_repository = TrackerRepository(JobApplication)
