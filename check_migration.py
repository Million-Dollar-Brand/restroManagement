import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        rows = result.fetchall()
        print("Current alembic versions:", rows)

asyncio.run(check())
