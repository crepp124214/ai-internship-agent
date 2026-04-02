"""User management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.business_logic.user import user_service
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.user import (
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserUpdate,
)


router = APIRouter()


@router.post("/", response_model=User)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a user."""
    try:
        return await user_service.create_user(db, user_data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"create user failed: {exc}",
        ) from exc


@router.post("/login/", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and issue an access token."""
    user = await user_service.authenticate_user(
        db, login_data.username, login_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=user_service.create_access_token(subject=str(user.id))
    )


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Return a user by id."""
    user = await user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
):
    """Update a user."""
    try:
        user = await user_service.update_user(db, user_id, user_data)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"update user failed: {exc}",
        ) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    try:
        deleted = await user_service.delete_user(db, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"delete user failed: {exc}",
        ) from exc


@router.get("/", response_model=list[User])
async def list_users(db: Session = Depends(get_db)):
    """List users."""
    return await user_service.get_users(db)
