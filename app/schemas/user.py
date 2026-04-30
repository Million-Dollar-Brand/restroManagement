from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""
    id: uuid.UUID
    avatar_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserBase):
    """Schema for public user profile"""
    id: uuid.UUID
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload"""
    username: Optional[str] = None
