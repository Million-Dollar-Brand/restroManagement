import asyncio
from sqlalchemy import text
from app.database import engine

async def check_tables():
    async with engine.begin() as conn:
        # Check if super_admins table exists
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'super_admins'
        """))
        rows = result.fetchall()
        print("super_admins table exists:", len(rows) > 0)
        if rows:
            print("Found tables:", rows)
        
        # List all tables
        result2 = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        all_tables = result2.fetchall()
        print("All tables in public schema:", [r[0] for r in all_tables])

asyncio.run(check_tables())
