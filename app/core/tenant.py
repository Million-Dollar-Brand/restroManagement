from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, set_search_path, reset_search_path
from app.core.security import decode_token
from app.config import settings
from app.models.public import Restaurant
from sqlalchemy import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user_tenant(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decode JWT token and extract user information including tenant_id.

    Expected JWT payload structure:
    {
        "sub": "username",
        "tenant_id": "uuid-string",  # For tenant users
        "role": "manager|waiter|chef|cashier",  # For tenant users
        "type": "access",
        "exp": timestamp
    }

    For super admin, tenant_id may be None.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    tenant_id = payload.get("tenant_id")  # May be None for super admin
    role = payload.get("role")  # May be None for super admin

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {
        "username": username,
        "tenant_id": tenant_id,
        "role": role,
        "is_super_admin": tenant_id is None
    }


async def get_tenant_session(
    user_info: dict = Depends(get_current_user_tenant),
    session: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """
    FastAPI dependency that provides a database session configured for the correct tenant schema.

    For tenant users: Sets search_path to tenant_<tenant_id>
    For super admin: Uses public schema (default)

    Returns the configured session.
    """
    if user_info["is_super_admin"]:
        # Super admin operates in public schema
        await reset_search_path(session)
    else:
        # Tenant user - switch to their schema
        tenant_id = user_info["tenant_id"]
        schema_name = f"{settings.tenant_schema_prefix}{tenant_id}"

        # Verify the tenant exists
        result = await session.execute(
            select(Restaurant).where(Restaurant.id == tenant_id, Restaurant.is_active == True)
        )
        restaurant = result.scalar_one_or_none()

        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant not found or inactive"
            )

        # Set search path to tenant schema
        await set_search_path(session, schema_name)

    return session


async def require_super_admin(user_info: dict = Depends(get_current_user_tenant)) -> dict:
    """Dependency that ensures the current user is a super admin"""
    if not user_info["is_super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return user_info


async def require_tenant_user(user_info: dict = Depends(get_current_user_tenant)) -> dict:
    """Dependency that ensures the current user is a tenant user (not super admin)"""
    if user_info["is_super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant user access required"
        )
    return user_info


def require_role(required_roles: list[str]):
    """
    Dependency factory that checks if user has one of the required roles.
    Usage: Depends(require_role(["manager", "waiter"]))
    """
    async def role_checker(user_info: dict = Depends(get_current_user_tenant)) -> dict:
        if user_info["is_super_admin"]:
            # Super admin has all permissions
            return user_info

        user_role = user_info.get("role")
        if not user_role or user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(required_roles)}"
            )
        return user_info

    return role_checker