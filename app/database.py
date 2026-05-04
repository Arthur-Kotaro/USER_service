# app/database.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncAttrs,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

load_dotenv()

# Формирование URL подключения к БД
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "user_service")
    DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)

# Базовый класс моделей с поддержкой AsyncAttrs (для awaitable_attrs)
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Dependency для получения сессии
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
