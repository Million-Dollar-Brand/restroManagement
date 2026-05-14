import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.begin() as conn:
        # Check if alembic_version exists
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        """))
        print("alembic_version table exists:", len(result.fetchall()) > 0)
        
        # Check version
        try:
            result2 = await conn.execute(text("SELECT version_num FROM alembic_version"))
            print("Current version:", result2.fetchall())
        except Exception as e:
            print("Error reading version:", e)

asyncio.run(check())
