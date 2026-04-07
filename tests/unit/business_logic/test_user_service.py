"""Unit tests for the user service."""

from unittest.mock import MagicMock, patch

import pytest

from src.business_logic.user.service import UserService
from src.presentation.schemas.user import UserCreate, UserUpdate


class TestUserService:
    def setup_method(self):
        self.service = UserService()
        self.mock_db = MagicMock()

    @pytest.mark.asyncio
    async def test_create_user(self):
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            name="Test User",
            phone="13800138000",
            bio="This is a test user",
        )

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.create.return_value = mock_user

            result = await self.service.create_user(self.mock_db, user_data)

            assert result is not None
            assert result.username == "testuser"
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_failure(self):
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            name="Test User",
        )

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.create.side_effect = Exception("database error")

            with pytest.raises(Exception) as exc_info:
                await self.service.create_user(self.mock_db, user_data)

            assert "Create user failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user(self):
        user_id = 1
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = "testuser"

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_user

            result = await self.service.get_user(self.mock_db, user_id)

            assert result is not None
            assert result.id == user_id
            mock_repo.get_by_id.assert_called_once_with(self.mock_db, user_id)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = await self.service.get_user(self.mock_db, 999)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_username(self):
        username = "testuser"
        mock_user = MagicMock()
        mock_user.username = username

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.get_by_field.return_value = [mock_user]

            result = await self.service.get_user_by_username(self.mock_db, username)

            assert result is not None
            assert result.username == username
            mock_repo.get_by_field.assert_called_once_with(
                self.mock_db, "username", username
            )

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self):
        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.get_by_field.return_value = []

            result = await self.service.get_user_by_username(self.mock_db, "nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_users(self):
        mock_users = [
            MagicMock(id=1, username="user1"),
            MagicMock(id=2, username="user2"),
            MagicMock(id=3, username="user3"),
        ]

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.get_all.return_value = mock_users

            result = await self.service.get_users(self.mock_db)

            assert len(result) == 3
            assert result[0].username == "user1"
            mock_repo.get_all.assert_called_once_with(self.mock_db)

    @pytest.mark.asyncio
    async def test_get_users_empty(self):
        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.get_all.return_value = []

            result = await self.service.get_users(self.mock_db)

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_user(self):
        user_data = UserUpdate(name="New Name", bio="New bio")
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "New Name"

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.update.return_value = mock_user

            result = await self.service.update_user(self.mock_db, 1, user_data)

            assert result is not None
            assert result.name == "New Name"
            mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        user_data = UserUpdate(name="New Name")

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.update.return_value = None

            result = await self.service.update_user(self.mock_db, 999, user_data)

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_user(self):
        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.delete.return_value = True

            result = await self.service.delete_user(self.mock_db, 1)

            assert result is True
            mock_repo.delete.assert_called_once_with(self.mock_db, 1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.delete.return_value = False

            result = await self.service.delete_user(self.mock_db, 999)

            assert result is False

    @pytest.mark.asyncio
    async def test_create_user_password_hashing(self):
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            name="Test User",
        )

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("src.business_logic.user.service.user_repository") as mock_repo:
            mock_repo.create.return_value = mock_user

            await self.service.create_user(self.mock_db, user_data)

            created_payload = mock_repo.create.call_args.args[1]
            assert created_payload["password_hash"] != "password123"
            assert created_payload["password_hash"] != "hashed_password123"
            assert self.service.verify_password(
                "password123", created_payload["password_hash"]
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_returns_user_for_valid_credentials(self):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.password_hash = self.service.get_password_hash("password123")

        with patch.object(
            self.service, "get_user_by_username", return_value=mock_user
        ) as mock_get_user:
            result = await self.service.authenticate_user(
                self.mock_db, "testuser", "password123"
            )

            assert result is mock_user
            mock_get_user.assert_awaited_once_with(self.mock_db, "testuser")

    @pytest.mark.asyncio
    async def test_authenticate_user_returns_none_for_invalid_password(self):
        mock_user = MagicMock()
        mock_user.password_hash = self.service.get_password_hash("password123")

        with patch.object(
            self.service, "get_user_by_username", return_value=mock_user
        ):
            result = await self.service.authenticate_user(
                self.mock_db, "testuser", "bad-password"
            )

            assert result is None

    def test_access_token_round_trip(self):
        token = self.service.create_access_token(subject="123")

        payload = self.service.decode_access_token(token)

        assert payload["sub"] == "123"

    def test_create_refresh_token(self):
        token = self.service.create_refresh_token(user_id=42)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_refresh_token_valid(self):
        token = self.service.create_refresh_token(user_id=42)
        user_id = self.service.verify_refresh_token(token)
        assert user_id == 42

    def test_verify_refresh_token_invalid(self):
        user_id = self.service.verify_refresh_token("invalid.token.here")
        assert user_id is None

    def test_revoke_refresh_token(self):
        mock_user = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        self.service.revoke_refresh_token(self.mock_db, user_id=1)
        assert mock_user.refresh_token_hash is None
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_get_password_hash(self):
        hashed = self.service.get_password_hash("testpassword")
        assert hashed != "testpassword"
        assert self.service.verify_password("testpassword", hashed)

    def test_verify_password_wrong(self):
        hashed = self.service.get_password_hash("testpassword")
        assert not self.service.verify_password("wrongpassword", hashed)
