from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.tenant import get_tenant_session
from app.models.tenant import Staff, UserRole
from app.core.tenant import require_tenant_user, require_role
from app.core.security import get_password_hash
from app.config import settings

router = APIRouter(prefix="/staff", tags=["staff"])


class StaffCreate(BaseModel):
    """Schema for creating staff user"""
    email: str
    username: str
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.WAITER


class StaffResponse(BaseModel):
    """Response schema for staff"""
    id: str
    email: str
    username: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: str


class StaffUpdate(BaseModel):
    """Schema for updating staff user"""
    email: str | None = None
    username: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager"]))
):
    """
    Create a new staff user (Manager only)

    - **email**: Valid email address (required, unique)
    - **username**: 3-50 characters (required, unique)
    - **password**: Minimum 8 characters (required)
    - **full_name**: Optional full name
    - **role**: Staff role (waiter, chef, cashier)
    """
    # Check if staff exists
    existing = await session.execute(
        select(Staff).where(
            (Staff.email == staff_data.email) | (Staff.username == staff_data.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists"
        )

    # Create staff user
    staff = Staff(
        email=staff_data.email,
        username=staff_data.username,
        full_name=staff_data.full_name,
        hashed_password=get_password_hash(staff_data.password),
        role=staff_data.role,
        is_active=True
    )
    session.add(staff)
    await session.commit()
    await session.refresh(staff)

    return StaffResponse(
        id=str(staff.id),
        email=staff.email,
        username=staff.username,
        full_name=staff.full_name,
        role=staff.role.value,
        is_active=staff.is_active,
        created_at=staff.created_at.isoformat()
    )


@router.get("", response_model=List[StaffResponse])
async def list_staff(
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """List all staff users"""
    result = await session.execute(select(Staff))
    staff_list = result.scalars().all()

    return [
        StaffResponse(
            id=str(s.id),
            email=s.email,
            username=s.username,
            full_name=s.full_name,
            role=s.role.value,
            is_active=s.is_active,
            created_at=s.created_at.isoformat()
        )
        for s in staff_list
    ]


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: str,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """Get staff user by ID"""
    try:
        from uuid import UUID
        staff_uuid = UUID(staff_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staff ID")

    result = await session.execute(select(Staff).where(Staff.id == staff_uuid))
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    return StaffResponse(
        id=str(staff.id),
        email=staff.email,
        username=staff.username,
        full_name=staff.full_name,
        role=staff.role.value,
        is_active=staff.is_active,
        created_at=staff.created_at.isoformat()
    )


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff_data: StaffUpdate,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager"]))
):
    """Update staff user (Manager only)"""
    try:
        from uuid import UUID
        staff_uuid = UUID(staff_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staff ID")

    result = await session.execute(select(Staff).where(Staff.id == staff_uuid))
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    # Update fields
    update_data = staff_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(staff, "hashed_password", get_password_hash(value))
        else:
            setattr(staff, field, value)

    await session.commit()
    await session.refresh(staff)

    return StaffResponse(
        id=str(staff.id),
        email=staff.email,
        username=staff.username,
        full_name=staff.full_name,
        role=staff.role.value,
        is_active=staff.is_active,
        created_at=staff.created_at.isoformat()
    )


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager"]))
):
    """Delete staff user (Manager only)"""
    try:
        from uuid import UUID
        staff_uuid = UUID(staff_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staff ID")

    result = await session.execute(select(Staff).where(Staff.id == staff_uuid))
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    # Soft delete - just deactivate
    staff.is_active = False
    await session.commit()

    return {"message": "Staff deactivated successfully"}