#!/usr/bin/env python3
"""
Initialization script for tenant tables.

This script ensures that all existing tenant schemas have the required tables
(staff, menu_items, orders, order_items) by creating them using TenantBase.metadata.create_all().

Usage:
    python scripts/init_tenant_tables.py [--dry-run] [--verbose]

Options:
    --dry-run: Show what would be done without making changes
    --verbose: Enable verbose logging
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models.public import Restaurant
from app.models.tenant import TenantBase
from app.config import settings


async def check_schema_exists(schema_name: str) -> bool:
    """Check if a PostgreSQL schema exists."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"),
                {"schema_name": schema_name}
            )
            return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking schema {schema_name}: {e}")
        return False


async def check_table_exists(schema_name: str, table_name: str) -> bool:
    """Check if a table exists in the specified schema."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = :schema_name AND table_name = :table_name
                """),
                {"schema_name": schema_name, "table_name": table_name}
            )
            return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking table {schema_name}.{table_name}: {e}")
        return False


async def create_tenant_tables_for_schema(schema_name: str, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Create tenant tables in the specified schema.

    Args:
        schema_name: Name of the schema to create tables in
        dry_run: If True, only show what would be done
        verbose: If True, enable verbose logging

    Returns:
        True if tables were created or already exist, False on error
    """
    try:
        if verbose:
            print(f"Processing schema: {schema_name}")

        # Check if schema exists
        if not await check_schema_exists(schema_name):
            print(f"Warning: Schema {schema_name} does not exist, skipping")
            return False

        # Check if staff table already exists
        if await check_table_exists(schema_name, "staff"):
            if verbose:
                print(f"  Tables already exist in schema {schema_name}, skipping")
            return True

        if dry_run:
            print(f"  Would create tenant tables in schema {schema_name}")
            return True

        if verbose:
            print(f"  Creating tenant tables in schema {schema_name}")

        # Set schema on metadata for this creation
        original_schema = TenantBase.metadata.schema
        TenantBase.metadata.schema = schema_name

        try:
            # Use engine.begin() to create tables (bypasses session transaction issues)
            async with engine.begin() as conn:
                # Set search path to the target schema
                await conn.execute(text(f"SET search_path TO {schema_name}"))
                await conn.run_sync(TenantBase.metadata.create_all)

            if verbose:
                print(f"  Successfully created tenant tables in schema {schema_name}")
            return True

        finally:
            # Reset schema to avoid affecting other operations
            TenantBase.metadata.schema = original_schema

    except Exception as e:
        print(f"Error creating tables in schema {schema_name}: {e}")
        return False


async def main(dry_run: bool = False, verbose: bool = False) -> None:
    """Main function to initialize tenant tables for all restaurants."""
    print("Initializing tenant tables for existing restaurants...")
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    print()

    success_count = 0
    error_count = 0
    skipped_count = 0
    would_create_count = 0

    try:
        # Get database session
        async with AsyncSessionLocal() as session:
            # Query all active restaurants
            result = await session.execute(
                select(Restaurant).where(Restaurant.is_active == True)
            )
            restaurants = result.scalars().all()

            if not restaurants:
                print("No active restaurants found.")
                return

            print(f"Found {len(restaurants)} active restaurant(s)")

            # Process each restaurant
            for restaurant in restaurants:
                if verbose:
                    print(f"\nRestaurant: {restaurant.name} (ID: {restaurant.id})")

                tables_existed = await check_table_exists(restaurant.schema_name, "staff")

                if tables_existed:
                    if verbose:
                        print(f"  Tables already exist in schema {restaurant.schema_name}, skipping")
                    success_count += 1
                    continue

                success = await create_tenant_tables_for_schema(
                    restaurant.schema_name,
                    dry_run=dry_run,
                    verbose=verbose
                )

                if success:
                    if dry_run:
                        would_create_count += 1
                    else:
                        success_count += 1
                else:
                    error_count += 1

        print("\nResults:")
        print(f"  Successful: {success_count}")
        print(f"  Skipped (already exist): {skipped_count}")
        if dry_run:
            print(f"  Would create: {would_create_count}")
        print(f"  Errors: {error_count}")

        if error_count > 0:
            print(f"\nCompleted with {error_count} error(s). Check output above for details.")
            sys.exit(1)
        else:
            print("\nAll tenant schemas processed successfully!")

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize tenant tables for existing restaurants")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Run the async main function
    asyncio.run(main(dry_run=args.dry_run, verbose=args.verbose))