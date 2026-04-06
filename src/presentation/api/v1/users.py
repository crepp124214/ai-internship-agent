"""User management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.business_logic.user import user_service
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.user import (
    User,
    UserCreate,
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Create user failed",
        )


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a user by id. Users can only view their own profile."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' profiles",
        )
    return current_user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a user. Users can only update their own profile."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify other users' profiles",
        )
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update user failed",
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a user. Users can only delete their own account."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other users' accounts",
        )
    try:
        deleted = await user_service.delete_user(db, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete user failed",
        )


@router.get("/", response_model=list[User])
async def list_users(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable bulk user listing for regular authenticated users."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User listing is not available",
    )
