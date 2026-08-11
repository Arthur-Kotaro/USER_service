# init_db.py (исправленная версия)
import asyncio
from app.database import engine, Base
from app.models import user, role, project, refresh_token, token_blacklist, login_history, department

async def init_db():
    async with engine.begin() as conn:
        # Создаем таблицы, если они не существуют
        await conn.run_sync(Base.metadata.create_all)
        print("✅ База данных успешно создана/обновлена!")

if __name__ == "__main__":
    asyncio.run(init_db())
