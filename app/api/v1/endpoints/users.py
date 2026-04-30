from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse, UserProfile
from app.api.v1.endpoints.auth import get_current_active_user
from app.core.uploads import save_upload_file, delete_file
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all users (admin only, paginated)

    - **skip**: Number of records to skip
    - **limit**: Maximum records to return (default 100)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile"""
    return current_user


@router.get("/{user_id}", response_model=UserProfile)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get public user profile by ID

    - **user_id**: UUID of the user
    """
    try:
        import uuid
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = db.query(User).filter(User.id == uid, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")

    if "username" in update_data:
        existing = db.query(User).filter(
            User.username == update_data["username"],
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete current user account"""
    # Delete avatar file if exists
    if current_user.avatar_url:
        await delete_file(current_user.avatar_url)

    db.delete(current_user)
    db.commit()
    return None


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload profile avatar

    - **file**: Image file (jpg, jpeg, png, webp), max 5MB
    """
    # Delete old avatar
    if current_user.avatar_url:
        await delete_file(current_user.avatar_url)

    # Save new avatar
    file_path = await save_upload_file(file, subfolder="profiles")
    current_user.avatar_url = file_path
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/avatar", response_model=UserResponse)
async def remove_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove profile avatar"""
    if current_user.avatar_url:
        await delete_file(current_user.avatar_url)
        current_user.avatar_url = None
        db.commit()
        db.refresh(current_user)
    return current_user
