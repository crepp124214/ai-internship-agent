"""Authentication API routes with refresh token support."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from src.data_access.entities.user import User
from src.presentation.api.deps import get_db, get_current_user
from src.business_logic.user import user_service
from src.presentation.schemas.user import (
    LoginRequest,
    LoginResponse,
    TokenRefreshResponse,
)
from src.utils.config_loader import get_settings


router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
    )


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate user and issue access token + refresh cookie."""
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

    _set_refresh_cookie(response, refresh_token)

    return LoginResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """Exchange refresh cookie for a new access token and rotate refresh cookie."""
    settings = get_settings()
    refresh_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = user_service.verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.refresh_token_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if not user_service.verify_password(refresh_token, user.refresh_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_access = user_service.create_access_token(str(user_id))
    new_refresh = user_service.create_refresh_token(user_id)
    user.refresh_token_hash = user_service.get_password_hash(new_refresh)
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_refresh_cookie(response, new_refresh)

    return TokenRefreshResponse(access_token=new_access)


@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke refresh token on logout and clear refresh cookie."""
    user_service.revoke_refresh_token(db, current_user.id)
    _clear_refresh_cookie(response)
    return {"msg": "Refresh token revoked"}
