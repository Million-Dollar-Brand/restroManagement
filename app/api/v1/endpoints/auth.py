from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.models.public import SuperAdmin, RestaurantManager
from app.models.tenant import Staff
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.tenant import oauth2_scheme

router = APIRouter(prefix="/auth", tags=["authentication"])


class SuperAdminCreate(BaseModel):
    """Schema for creating super admin user"""
    email: str
    username: str
    password: str
    full_name: str | None = None


class SuperAdminResponse(BaseModel):
    """Response schema for super admin"""
    id: str
    email: str
    username: str
    full_name: str | None
    is_active: bool
    created_at: str


async def get_current_super_admin(token: str = Depends(oauth2_scheme)) -> SuperAdmin:
    """Get current super admin from JWT token"""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # For super admin, tenant_id should be None
    if payload.get("tenant_id") is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )

    return {"username": username, "is_super_admin": True}


async def authenticate_super_admin(db: AsyncSession, username: str, password: str) -> SuperAdmin | None:
    """Authenticate super admin user"""
    result = await db.execute(
        select(SuperAdmin).where(SuperAdmin.username == username, SuperAdmin.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def authenticate_restaurant_manager(db: AsyncSession, username: str, password: str) -> RestaurantManager | None:
    """Authenticate restaurant manager user"""
    result = await db.execute(
        select(RestaurantManager).where(RestaurantManager.username == username, RestaurantManager.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def authenticate_staff(db: AsyncSession, username: str, password: str) -> tuple[Staff, str] | None:
    """Authenticate staff user and return user with tenant_id"""
    result = await db.execute(
        select(Staff).where(Staff.username == username, Staff.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.hashed_password):
        # Get tenant_id from current search path (set by tenant routing)
        # For now, we'll need to extract it from the schema context
        # This is a simplified approach - in production you'd track tenant_id in staff table
        return (user, None)  # tenant_id will be resolved by routing logic
    return None


async def get_user_by_username(db: AsyncSession, username: str) -> SuperAdmin | RestaurantManager | Staff | None:
    """Get any user type by username for token refresh"""
    # Check super admin
    result = await db.execute(
        select(SuperAdmin).where(SuperAdmin.username == username, SuperAdmin.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    # Check restaurant manager
    result = await db.execute(
        select(RestaurantManager).where(RestaurantManager.username == username, RestaurantManager.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    # Check staff (this might need tenant context)
    result = await db.execute(
        select(Staff).where(Staff.username == username, Staff.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    return None


@router.post("/super-admin/register", response_model=SuperAdminResponse, status_code=status.HTTP_201_CREATED)
async def register_super_admin(
    user_data: SuperAdminCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new super admin user

    - **email**: Valid email address (required, unique)
    - **username**: 3-50 characters (required, unique)
    - **password**: Minimum 8 characters (required)
    - **full_name**: Optional full name
    """
    # Check if super admin exists
    existing = await db.execute(
        select(SuperAdmin).where(
            (SuperAdmin.email == user_data.email) | (SuperAdmin.username == user_data.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    # Create super admin
    super_admin = SuperAdmin(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )
    db.add(super_admin)
    await db.commit()
    await db.refresh(super_admin)
    return SuperAdminResponse(
        id=str(super_admin.id),
        email=super_admin.email,
        username=super_admin.username,
        full_name=super_admin.full_name,
        is_active=super_admin.is_active,
        created_at=super_admin.created_at.isoformat()
    )


@router.post("/super-admin/login", response_model=Token)
async def super_admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Super admin login and receive JWT tokens

    - **username**: Your username
    - **password**: Your password

    Returns access_token and refresh_token
    """
    user = await authenticate_super_admin(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        tenant_id=None,  # Super admin has no tenant
        role=None  # Super admin has all permissions
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/restaurant/login", response_model=Token)
async def restaurant_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Restaurant manager login

    Authenticates restaurant managers.
    """
    # Try restaurant manager
    manager = await authenticate_restaurant_manager(db, form_data.username, form_data.password)
    if manager:
        access_token = create_access_token(
            data={"sub": manager.username},
            tenant_id=str(manager.restaurant_id),
            role="manager"
        )
        refresh_token = create_refresh_token(data={"sub": manager.username})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Get user by username
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Create new tokens - tenant info will be included based on user type
    if isinstance(user, SuperAdmin):
        access_token = create_access_token(data={"sub": user.username})
    elif isinstance(user, RestaurantManager):
        access_token = create_access_token(
            data={"sub": user.username},
            tenant_id=str(user.restaurant_id),
            role="manager"
        )
    else:  # Staff
        access_token = create_access_token(
            data={"sub": user.username},
            tenant_id=None,  # Will be resolved by routing logic
            role=user.role.value
        )

    new_refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }