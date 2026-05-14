#!/usr/bin/env python3
# check_db_async_fixed.py - Асинхронная проверка структуры PostgreSQL базы данных (исправленная версия)

import asyncio
from sqlalchemy import text
from app.database import engine

async def print_section(title: str, char: str = "=", width: int = 80):
    """Печать секции с заголовком"""
    print(f"\n{char * width}")
    print(f" {title} ".center(width, char))
    print(f"{char * width}")

async def analyze_database():
    """Полный анализ структуры базы данных"""
    
    await print_section("🔍 АНАЛИЗ СТРУКТУРЫ БАЗЫ ДАННЫХ", "=")
    
    try:
        async with engine.connect() as conn:
            # Получаем версию PostgreSQL
            version = await conn.execute(text("SELECT version()"))
            version_str = version.scalar()
            print(f"\n✅ Подключено: {version_str[:80]}...")
            
            # Получаем имя базы данных
            db_name = await conn.execute(text("SELECT current_database()"))
            print(f"📚 База данных: {db_name.scalar()}")
            
            # Получаем список таблиц
            tables_result = await conn.execute(
                text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
            )
            tables = [row[0] for row in tables_result]
            
    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
        return

    # 1. Список всех таблиц
    await print_section("📊 ТАБЛИЦЫ В БАЗЕ ДАННЫХ", "-")
    for i, table in enumerate(tables, 1):
        print(f"  {i:2}. {table}")

    # 2. Детальная информация по каждой таблице
    await print_section("📋 ДЕТАЛЬНАЯ СТРУКТУРА ТАБЛИЦ", "-")
    
    async with engine.connect() as conn:
        for table in tables:
            print(f"\n📌 Таблица: {table}")
            print(f"   {'-' * 60}")
            
            # Получаем колонки через информационную схему PostgreSQL
            columns_result = await conn.execute(
                text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = :table
                    ORDER BY ordinal_position
                """),
                {"table": table}
            )
            columns = columns_result.fetchall()
            
            print(f"   🗂️ Колонки ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"      • {col[0]:30} {col[1]:20} {nullable}{default}")
            
            # 🔧 ИСПРАВЛЕНО: Имена таблиц вставляем напрямую, без параметров
            # Получаем первичные ключи
            pk_query = f"""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = '{table}'::regclass AND i.indisprimary
            """
            pk_result = await conn.execute(text(pk_query))
            pk_columns = [row[0] for row in pk_result]
            if pk_columns:
                print(f"   🔑 Первичный ключ: {', '.join(pk_columns)}")
            
            # 🔧 ИСПРАВЛЕНО: Имена таблиц вставляем напрямую
            fk_query = f"""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = '{table}'
            """
            fk_result = await conn.execute(text(fk_query))
            fks = fk_result.fetchall()
            if fks:
                print(f"   🔗 Внешние ключи:")
                for fk in fks:
                    print(f"      • {fk[0]} → {fk[1]}.{fk[2]}")
            
            # Количество записей
            try:
                count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                print(f"   📈 Количество записей: {count}")
            except Exception as e:
                print(f"   ⚠️ Не удалось получить количество: {e}")

    # 3. Статистика по ключевым таблицам
    await print_section("📈 СТАТИСТИКА", "-")
    
    stats_queries = [
        ("Всего пользователей", "SELECT COUNT(*) FROM users"),
        ("Активных пользователей", "SELECT COUNT(*) FROM users WHERE status = 'active'"),
        ("Заблокированных пользователей", "SELECT COUNT(*) FROM users WHERE status = 'blocked'"),
        ("Архивированных пользователей", "SELECT COUNT(*) FROM users WHERE status = 'archived'"),
        ("Ролей", "SELECT COUNT(*) FROM roles"),
        ("Проектов", "SELECT COUNT(*) FROM projects"),
        ("Отделов", "SELECT COUNT(*) FROM departament"),
        ("Refresh токенов", "SELECT COUNT(*) FROM refresh_tokens"),
        ("Активных refresh токенов", "SELECT COUNT(*) FROM refresh_tokens WHERE revoked = false"),
        ("Токенов в черном списке", "SELECT COUNT(*) FROM token_blacklist"),
    ]
    
    async with engine.connect() as conn:
        for label, query in stats_queries:
            try:
                result = await conn.execute(text(query))
                count = result.scalar()
                print(f"   • {label:30}: {count}")
            except Exception as e:
                print(f"   • {label:30}: Ошибка - {e}")

    await print_section("✨ АНАЛИЗ ЗАВЕРШЕН", "=")

async def check_user_model_compatibility():
    """Проверка совместимости модели User с существующей таблицей"""
    await print_section("🔄 ПРОВЕРКА СОВМЕСТИМОСТИ МОДЕЛИ USER", "-")
    
    async with engine.connect() as conn:
        columns_result = await conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
        )
        db_columns = {row[0] for row in columns_result}
    
    expected_columns = {
        'user_id', 'user_name', 'password_hash', 'email', 'gender', 'birth_date',
        'dept_code', 'status', 'blocked_at', 'blocked_reason', 'blocked_by',
        'block_expires_at', 'created_at', 'updated_at', 'last_login_at'
    }
    
    missing_in_db = expected_columns - db_columns
    extra_in_db = db_columns - expected_columns
    
    if missing_in_db:
        print(f"\n   ⚠️ В БД отсутствуют поля (будут добавлены в модель?):")
        for col in sorted(missing_in_db):
            print(f"      - {col}")
    else:
        print(f"\n   ✅ Все ожидаемые поля присутствуют в БД")
    
    if extra_in_db:
        print(f"\n   ℹ️ В БД есть дополнительные поля (можно добавить в модель):")
        for col in sorted(extra_in_db):
            print(f"      - {col}")
    
    if not missing_in_db and not extra_in_db:
        print("\n   ✅ Модель User полностью совместима с БД")

async def main():
    await analyze_database()
    await check_user_model_compatibility()

if __name__ == "__main__":
    asyncio.run(main())
