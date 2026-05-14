from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import os

# Create declarative base (always available)
Base = declarative_base()

# Only create async engine if not running migrations
# Only create async engine if not running migrations
if os.environ.get("ALEMBIC_RUNNING") != "1":
    # Ensure database URL has ssl=require for Neon (asyncpg compatibility)
    db_url = settings.database_url
    if "ssl=" not in db_url and "sslmode" not in db_url:
        if "?" in db_url:
            db_url += "&ssl=require"
        else:
            db_url += "?ssl=require"
    
    # Async engine for PostgreSQL (Neon requires SSL)
    engine: AsyncEngine = create_async_engine(
        db_url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,
    )
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
else:
    # For migrations, these won't be used
    engine = None
    AsyncSessionLocal = None


async def get_db() -> AsyncSession:
    """
    Dependency to get async database session.
    Yields a session and ensures it is closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def set_search_path(session: AsyncSession, schema_name: str) -> None:
    """
    Set the search_path for the given session to the specified schema.
    This ensures that subsequent queries use the specified schema.
    """
    await session.execute(text(f"SET search_path TO {schema_name}"))


async def reset_search_path(session: AsyncSession) -> None:
    """
    Reset the search_path to the default (public) schema.
    """
    await session.execute(text("SET search_path TO public"))