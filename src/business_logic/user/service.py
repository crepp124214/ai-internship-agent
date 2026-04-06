"""User service logic, including minimal authentication helpers."""

from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, List, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.data_access.entities.user import User as UserModel
from src.data_access.repositories.user_repository import user_repository
from src.presentation.schemas.user import UserCreate, UserUpdate
from src.utils.config_loader import get_settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


class UserService:
    """Business logic for user management and minimal authentication."""

    def get_password_hash(self, password: str) -> str:
        """Hash a password for storage."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify a plain password against its stored hash."""
        return pwd_context.verify(plain_password, password_hash)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _token_common_claims(self) -> dict[str, Any]:
        settings = get_settings()
        now = self._now()
        return {
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "iat": now,
            "nbf": now,
            "jti": str(uuid.uuid4()),
        }

    def create_access_token(
        self,
        subject: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a signed JWT access token."""
        settings = get_settings()
        expire_at = self._now() + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            **self._token_common_claims(),
            "sub": subject,
            "exp": expire_at,
            "type": "access",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT access token."""
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
        except JWTError as exc:
            raise ValueError("Invalid authentication credentials") from exc

        subject = payload.get("sub")
        if not subject or payload.get("type") != "access":
            raise ValueError("Invalid authentication credentials")
        return payload

    # Refresh token related helpers
    def create_refresh_token(self, user_id: int) -> str:
        """Create a signed JWT refresh token for the given user_id."""
        settings = get_settings()
        expire_at = self._now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            **self._token_common_claims(),
            "sub": str(user_id),
            "exp": expire_at,
            "type": "refresh",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    def verify_refresh_token(self, token: str) -> Optional[int]:
        """Verify a refresh token and return user_id if valid, else None."""
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
        except JWTError:
            return None

        if payload.get("type") != "refresh":
            return None

        sub = payload.get("sub")
        if not sub:
            return None

        try:
            return int(sub)
        except ValueError:
            return None

    def revoke_refresh_token(self, db: Session, user_id: int) -> None:
        """Revoke a user's refresh token by clearing its stored hash."""
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            user.refresh_token_hash = None
            db.add(user)
            db.commit()
            db.refresh(user)

    async def create_user(self, db: Session, user_data: UserCreate) -> UserModel:
        """Create a user with a real password hash."""
        try:
            user = user_repository.create(
                db,
                {
                    "username": user_data.username,
                    "email": user_data.email,
                    "password_hash": self.get_password_hash(user_data.password),
                    "name": user_data.name,
                    "phone": user_data.phone,
                    "bio": user_data.bio,
                },
            )
            return user
        except Exception:
            raise Exception("Create user failed") from None

    async def get_user(self, db: Session, user_id: int) -> Optional[UserModel]:
        """Look up a user by id."""
        return user_repository.get_by_id(db, user_id)

    async def get_user_by_username(
        self, db: Session, username: str
    ) -> Optional[UserModel]:
        """Look up a user by username."""
        users = user_repository.get_by_field(db, "username", username)
        return users[0] if users else None

    async def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> Optional[UserModel]:
        """Return the user when credentials are valid."""
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    async def get_users(self, db: Session) -> List[UserModel]:
        """List all users."""
        return user_repository.get_all(db)

    async def update_user(
        self, db: Session, user_id: int, user_data: UserUpdate
    ) -> Optional[UserModel]:
        """Update user profile fields."""
        return user_repository.update(db, user_id, user_data.model_dump(exclude_unset=True))

    async def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete a user by id."""
        return user_repository.delete(db, user_id)


user_service = UserService()
