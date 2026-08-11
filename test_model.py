import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT user_id, full_name FROM users LIMIT 1"))
        row = result.first()
        print("Столбцы в таблице:", row.keys() if row else "Таблица пуста")

if __name__ == "__main__":
    asyncio.run(test())
