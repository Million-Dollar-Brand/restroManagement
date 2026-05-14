import asyncio
from sqlalchemy import text
from app.database import engine

async def check_alembic_version():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            rows = result.fetchall()
            print("Current alembic_version:", rows)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check_alembic_version())
