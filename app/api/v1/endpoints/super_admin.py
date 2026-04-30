import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel, Field
from app.database import get_db, set_search_path
from app.core.tenant import require_super_admin, get_tenant_session
from app.models.public import Restaurant, RestaurantManager
from app.models.tenant import TenantBase, Staff, UserRole
from app.core.security import get_password_hash
from app.config import settings
import subprocess
import os
import asyncio


router = APIRouter(prefix="/super-admin", tags=["super-admin"])


class RestaurantCreate(BaseModel):
    """Schema for creating a new restaurant"""
    name: str = Field(..., min_length=1, max_length=100, description="Restaurant name")
    description: str = Field(None, description="Optional restaurant description")

    # Initial manager details
    manager_email: str = Field(..., description="Manager's email address")
    manager_username: str = Field(..., min_length=3, max_length=50, description="Manager's username")
    manager_password: str = Field(..., min_length=8, description="Manager's password")
    manager_full_name: str = Field(None, description="Manager's full name")


class RestaurantResponse(BaseModel):
    """Response schema for restaurant creation"""
    id: str
    name: str
    description: str | None
    schema_name: str
    manager_id: str
    created_at: str


async def create_postgres_schema(schema_name: str, session: AsyncSession) -> None:
    """
    Create a new PostgreSQL schema.

    Args:
        schema_name: Name of the schema to create
        session: Database session

    Raises:
        HTTPException: If schema creation fails
    """
    try:
        await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schema: {str(e)}"
        )


async def run_alembic_migration(schema_name: str) -> None:
    """
    Run Alembic migrations for the new tenant schema.

    This function temporarily modifies the Alembic configuration to target
    the new schema and runs the migrations.

    Args:
        schema_name: Name of the schema to migrate

    Raises:
        HTTPException: If migration fails
    """
    try:
        # Set environment variable for schema targeting
        env = os.environ.copy()
        env["TENANT_SCHEMA"] = schema_name

        # Run alembic upgrade head command
        # Note: This assumes alembic is configured to use the tenant schema
        # when TENANT_SCHEMA environment variable is set
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.getcwd(),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise Exception(f"Alembic migration failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Migration timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


async def create_tenant_tables(schema_name: str, session: AsyncSession) -> None:
    """
    Create tenant-specific tables in the new schema.
    This is an alternative to running Alembic migrations.

    Args:
        schema_name: Name of the schema
        session: Database session
    """
    try:
        # Set search path to new schema
        await set_search_path(session, schema_name)

        # Create tables for tenant models
        async with session.begin():
            # Create all tenant tables
            await session.run_sync(TenantBase.metadata.create_all)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant tables: {str(e)}"
        )
    finally:
        # Reset search path
        await set_search_path(session, "public")


@router.post("/restaurants", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(require_super_admin)
):
    """
    Create a new restaurant with its own database schema.

    This endpoint:
    1. Creates a new PostgreSQL schema
    2. Creates tenant-specific tables via Alembic migrations
    3. Creates the restaurant record in public schema
    4. Creates the initial restaurant manager

    Only super admins can access this endpoint.
    """
    # Generate IDs
    restaurant_id = uuid.uuid4()
    manager_id = uuid.uuid4()
    schema_name = f"{settings.tenant_schema_prefix}{restaurant_id}"

    try:
        # Start transaction for public schema operations
        async with session.begin():
            # Check for duplicate email/username
            existing_manager = await session.execute(
                select(RestaurantManager).where(
                    (RestaurantManager.email == restaurant_data.manager_email) |
                    (RestaurantManager.username == restaurant_data.manager_username)
                )
            )
            if existing_manager.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Manager email or username already exists"
                )

            # Create the PostgreSQL schema
            await create_postgres_schema(schema_name, session)

            # Create tenant tables (alternative to Alembic - uncomment if preferred)
            # await create_tenant_tables(schema_name, session)

            # Run Alembic migrations on the new schema
            await run_alembic_migration(schema_name)

            # Create restaurant record
            restaurant = Restaurant(
                id=restaurant_id,
                name=restaurant_data.name,
                description=restaurant_data.description,
                schema_name=schema_name,
                is_active=True
            )
            session.add(restaurant)

            # Create manager record
            manager = RestaurantManager(
                id=manager_id,
                email=restaurant_data.manager_email,
                username=restaurant_data.manager_username,
                hashed_password=get_password_hash(restaurant_data.manager_password),
                full_name=restaurant_data.manager_full_name,
                restaurant_id=restaurant_id,
                is_active=True
            )
            session.add(manager)

            # Update restaurant with manager reference
            restaurant.manager_id = manager_id

        # Create initial staff user in tenant schema
        async with session.begin():
            await set_search_path(session, schema_name)

            # Create the manager as staff in tenant schema
            tenant_manager = Staff(
                id=manager_id,  # Same ID as public manager
                email=restaurant_data.manager_email,
                username=restaurant_data.manager_username,
                hashed_password=get_password_hash(restaurant_data.manager_password),
                full_name=restaurant_data.manager_full_name,
                role=UserRole.MANAGER,
                is_active=True
            )
            session.add(tenant_manager)

        # Reset search path
        await set_search_path(session, "public")

        return RestaurantResponse(
            id=str(restaurant_id),
            name=restaurant.name,
            description=restaurant.description,
            schema_name=restaurant.schema_name,
            manager_id=str(manager_id),
            created_at=restaurant.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on failure
        try:
            async with session.begin():
                await session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
        except:
            pass  # Ignore cleanup errors

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create restaurant: {str(e)}"
        )


@router.get("/restaurants")
async def list_restaurants(
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(require_super_admin)
):
    """List all restaurants (super admin only)"""
    result = await session.execute(
        select(Restaurant).where(Restaurant.is_active == True)
    )
    restaurants = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "schema_name": r.schema_name,
            "created_at": r.created_at.isoformat()
        }
        for r in restaurants
    ]


@router.delete("/restaurants/{restaurant_id}")
async def deactivate_restaurant(
    restaurant_id: str,
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(require_super_admin)
):
    """Deactivate a restaurant (super admin only)"""
    try:
        uuid_restaurant_id = uuid.UUID(restaurant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid restaurant ID")

    result = await session.execute(
        select(Restaurant).where(Restaurant.id == uuid_restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant.is_active = False
    await session.commit()

    return {"message": "Restaurant deactivated successfully"}