"""Reset database by dropping all tables and types"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def reset_database():
    async with engine.begin() as conn:
        # Drop all tables in all schemas (public and tenant schemas)
        await conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                -- Drop all tables in public schema
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
                
                -- Drop all enums/types
                FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e') LOOP
                    EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
                
                -- Drop alembic_version if exists
                DROP TABLE IF EXISTS alembic_version CASCADE;
            END $$;
        """))
        print("Database cleaned successfully.")

asyncio.run(reset_database())
