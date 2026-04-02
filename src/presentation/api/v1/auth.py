"""Authentication API routes with refresh token support."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.data_access.entities.user import User
from src.presentation.api.deps import get_db, get_current_user
from src.business_logic.user import user_service
from src.presentation.schemas.user import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and issue access + refresh tokens."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user_service.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = user_service.create_access_token(str(user.id))
    refresh_token = user_service.create_refresh_token(user.id)

    # Store hash of refresh token
    user.refresh_token_hash = user_service.get_password_hash(refresh_token)
    db.add(user)
    db.commit()
    db.refresh(user)

    return LoginResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    user_id = user_service.verify_refresh_token(req.refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.refresh_token_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if not user_service.verify_password(req.refresh_token, user.refresh_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_access = user_service.create_access_token(str(user_id))
    new_refresh = user_service.create_refresh_token(user_id)
    user.refresh_token_hash = user_service.get_password_hash(new_refresh)
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenRefreshResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke refresh token on logout."""
    user_service.revoke_refresh_token(db, current_user.id)
    return {"msg": "Refresh token revoked"}
