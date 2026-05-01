# app/database.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# Получение URL из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Собираем URL из отдельных параметров
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "user_service")
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Создание engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False  # Установите True для логирования SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> bool:
    """Тест подключения к БД"""
    try:
        with engine.connect() as conn:
            # Для PostgreSQL
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Подключение успешно: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def inspect_database():
    """Инспекция существующей БД"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        print("   (нет таблиц)")
    else:
        for table in tables:
            print(f"  - {table}")
            # Опционально: показать колонки
            columns = inspector.get_columns(table)
            print(f"    Колонки: {', '.join([col['name'] for col in columns[:5]])}")
            if len(columns) > 5:
                print(f"    ... и {len(columns) - 5} других")
