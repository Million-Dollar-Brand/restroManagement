from logging.config import fileConfig
from sqlalchemy import engine_from_config, text, create_engine
from sqlalchemy import pool
from alembic import context
import os

# Set flag to prevent async engine creation during migrations
os.environ["ALEMBIC_RUNNING"] = "1"

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from app settings to ensure consistency
from app.config import settings
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Determine if we're migrating a tenant schema
tenant_schema = os.environ.get("TENANT_SCHEMA")

if tenant_schema:
    # Tenant schema migration
    from app.models.tenant import TenantBase
    target_metadata = TenantBase.metadata
    schema_name = tenant_schema
else:
    # Public schema migration (default)
    from app.models.public import SuperAdmin, Restaurant, RestaurantManager
    from app.models.user import User  # Legacy user model for backward compatibility
    from app.database import Base
    target_metadata = Base.metadata
    schema_name = "public"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Set search path for tenant migrations
        if tenant_schema:
            connection.execute(text(f"SET search_path TO {schema_name}"))
            # Ensure schema exists
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
