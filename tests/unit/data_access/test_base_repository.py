"""Tests for BaseRepository."""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from src.data_access.repositories.base_repository import (
    BaseRepository,
    PaginationResult,
    create_repository,
)
from src.data_access.entities.user import User


class TestPaginationResult:
    """Test PaginationResult class."""

    def test_to_dict(self):
        result = PaginationResult(
            items=[],
            total=10,
            page=1,
            page_size=5,
            total_pages=2,
        )
        d = result.to_dict()
        assert d["total"] == 10
        assert d["page"] == 1
        assert d["page_size"] == 5
        assert d["total_pages"] == 2
        assert d["items"] == []


class TestBaseRepository:
    """Test BaseRepository CRUD operations."""

    def setup_method(self):
        self.repo = BaseRepository(User)
        self.mock_db = MagicMock(spec=Session)

    def test_get_by_id_returns_none_when_not_found(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.get_by_id(self.mock_db, 999)
        assert result is None

    def test_get_all_returns_list(self):
        mock_user = MagicMock()
        self.mock_db.query.return_value.all.return_value = [mock_user]
        result = self.repo.get_all(self.mock_db)
        assert len(result) == 1
        assert result[0] == mock_user

    def test_get_all_with_order_by(self):
        self.mock_db.query.return_value.order_by.return_value.all.return_value = []
        self.repo.get_all(self.mock_db, order_by="username")
        assert self.mock_db.query.return_value.order_by.called

    def test_get_by_field(self):
        self.mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        self.repo.get_by_field(self.mock_db, "username", "test")
        assert self.mock_db.query.return_value.filter.called

    def test_get_by_field_with_limit(self):
        self.mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        self.repo.get_by_field(self.mock_db, "username", "test", limit=10)
        assert self.mock_db.query.return_value.filter.return_value.limit.called

    def test_get_by_fields(self):
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        self.repo.get_by_fields(self.mock_db, {"username": "test", "email": "a@b.com"})
        assert self.mock_db.query.return_value.filter.called

    def test_get_by_fields_with_limit(self):
        self.mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        self.repo.get_by_fields(self.mock_db, {"username": "test"}, limit=5)
        assert self.mock_db.query.return_value.filter.return_value.limit.called

    def test_create(self):
        data = {"username": "test", "email": "test@example.com"}
        result = self.repo.create(self.mock_db, data)
        assert result.username == "test"
        assert result.email == "test@example.com"
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_update_returns_none_when_not_found(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.update(self.mock_db, 999, {"username": "new"})
        assert result is None

    def test_update_updates_and_refreshes(self):
        mock_instance = MagicMock()
        mock_instance.id = 1
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        result = self.repo.update(self.mock_db, 1, {"username": "updated"})
        assert mock_instance.username == "updated"
        self.mock_db.commit.assert_called()
        self.mock_db.refresh.assert_called()

    def test_delete_returns_false_when_not_found(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.delete(self.mock_db, 999)
        assert result is False

    def test_delete_deletes_and_returns_true(self):
        mock_instance = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        result = self.repo.delete(self.mock_db, 1)
        assert result is True
        self.mock_db.delete.assert_called_once()
        self.mock_db.commit.assert_called()

    def test_exists_returns_true(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        result = self.repo.exists(self.mock_db, 1)
        assert result is True

    def test_exists_returns_false(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.exists(self.mock_db, 999)
        assert result is False

    def test_exists_by_field(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        result = self.repo.exists_by_field(self.mock_db, "username", "test")
        assert result is True

    def test_exists_by_field_returns_false(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.exists_by_field(self.mock_db, "username", "notexist")
        assert result is False

    def test_count(self):
        self.mock_db.query.return_value.count.return_value = 5
        result = self.repo.count(self.mock_db)
        assert result == 5

    def test_count_by_field(self):
        self.mock_db.query.return_value.filter.return_value.count.return_value = 3
        result = self.repo.count_by_field(self.mock_db, "username", "test")
        assert result == 3

    def test_bulk_create(self):
        mock_instance = MagicMock()
        self.repo.model.side_effect = [mock_instance, mock_instance]
        data_list = [
            {"username": "user1", "email": "u1@example.com"},
            {"username": "user2", "email": "u2@example.com"},
        ]
        result = self.repo.bulk_create(self.mock_db, data_list)
        assert len(result) == 2
        self.mock_db.bulk_save_objects.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_bulk_update(self):
        self.mock_db.query.return_value.filter.return_value.update.return_value = 3
        result = self.repo.bulk_update(self.mock_db, [1, 2, 3], {"is_active": False})
        assert result == 3
        self.mock_db.commit.assert_called()

    def test_bulk_delete(self):
        self.mock_db.query.return_value.filter.return_value.delete.return_value = 2
        result = self.repo.bulk_delete(self.mock_db, [1, 2])
        assert result == 2
        self.mock_db.commit.assert_called()

    def test_delete_by_field(self):
        self.mock_db.query.return_value.filter.return_value.delete.return_value = 1
        result = self.repo.delete_by_field(self.mock_db, "username", "test")
        assert result == 1
        self.mock_db.commit.assert_called()


class TestCreateRepository:
    """Test create_repository factory function."""

    def test_create_repository_returns_instance(self):
        repo = create_repository(User)
        assert isinstance(repo, BaseRepository)
        assert repo.model == User
