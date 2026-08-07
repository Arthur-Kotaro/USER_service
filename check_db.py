#!/usr/bin/env python3
# app/check_db.py - Скрипт для проверки структуры БД
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def check_database():
    """Проверка подключения и структуры БД"""
    
    # Получаем параметры подключения
    database_url = os.getenv("DATABASE_URL")
    
    # Определяем переменные
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "user_service")
    
    # Если DATABASE_URL не задан или содержит asyncpg, формируем правильный URL
    if not database_url or "+asyncpg" in database_url:
        database_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    print(f"Подключение к БД: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    try:
        # Подключаемся к БД (asyncpg работает только с postgresql://, не с postgresql+asyncpg)
        conn = await asyncpg.connect(database_url)
        print("✅ Успешное подключение к базе данных")
        
        # Проверяем версию PostgreSQL
        version = await conn.fetchval("SELECT version()")
        print(f"📦 Версия PostgreSQL: {version.split(',')[0]}")
        
        # Проверяем список таблиц
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print("\n📋 Существующие таблицы:")
        for table in tables:
            print(f"  - {table['tablename']}")
        
        # Проверяем наличие обязательных таблиц
        required_tables = [
            'users', 'roles', 'users_roles',
            'projects', 'user_projects',
            'department', 'token_blacklist', 'refresh_tokens',
            'login_history', 'audit_log'
        ]
        
        existing_tables = [t['tablename'] for t in tables]
        
        print("\n🔍 Проверка обязательных таблиц:")
        for table in required_tables:
            if table in existing_tables:
                print(f"  ✅ {table} - существует")
            else:
                print(f"  ❌ {table} - ОТСУТСТВУЕТ!")
        
        # Проверяем структуру таблицы users
        print("\n👥 Структура таблицы users:")
        user_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        actual_columns = [c['column_name'] for c in user_columns]
        
        # Проверка отсутствия поля status
        if 'status' in actual_columns:
            print("  ⚠️ Поле 'status' всё ещё существует! (должно быть удалено)")
        else:
            print("  ✅ Поле 'status' успешно удалено")
        
        # Проверка наличия deleted_at
        if 'deleted_at' in actual_columns:
            print("  ✅ Поле 'deleted_at' добавлено (soft delete)")
        else:
            print("  ❌ Поле 'deleted_at' отсутствует!")
        
        # Проверка наличия blocked_at
        if 'blocked_at' in actual_columns:
            print("  ✅ Поле 'blocked_at' существует (блокировка)")
        
        for col in user_columns[:12]:
            print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        
        # Проверяем структуру таблицы roles
        print("\n🔐 Структура таблицы roles:")
        role_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'roles'
            ORDER BY ordinal_position
        """)
        
        role_col_names = [c['column_name'] for c in role_columns]
        
        for col in role_columns:
            print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        
        if 'role_title_ru' in role_col_names:
            print("  ✅ Поле 'role_title_ru' добавлено")
        else:
            print("  ❌ Поле 'role_title_ru' отсутствует!")
        
        if 'role_code' in role_col_names:
            print("  ✅ Поле 'role_code' добавлено")
        else:
            print("  ❌ Поле 'role_code' отсутствует!")
        
        # Проверяем структуру таблицы projects
        print("\n📁 Структура таблицы projects:")
        project_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'projects'
            ORDER BY ordinal_position
        """)
        
        project_col_names = [c['column_name'] for c in project_columns]
        
        if 'status' in project_col_names:
            print("  ✅ Поле 'status' добавлено в projects")
            # Проверяем тип ENUM
            status_type = await conn.fetchval("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'projects' AND column_name = 'status'
            """)
            print(f"  📊 Тип поля status: {status_type}")
        else:
            print("  ❌ Поле 'status' отсутствует в projects!")
        
        for col in project_columns:
            print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        
        # Проверяем наличие login_history
        print("\n📜 Таблица login_history:")
        if 'login_history' in existing_tables:
            history_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'login_history'
                ORDER BY ordinal_position
            """)
            for col in history_columns:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        else:
            print("  ❌ Таблица login_history отсутствует!")
        
        # Проверяем наличие audit_log
        print("\n📝 Таблица audit_log:")
        if 'audit_log' in existing_tables:
            audit_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'audit_log'
                ORDER BY ordinal_position
                LIMIT 8
            """)
            for col in audit_columns:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        else:
            print("  ❌ Таблица audit_log отсутствует!")
        
        # Проверяем индексы
        print("\n🔍 Проверка индексов:")
        
        # Индекс для deleted_at
        deleted_idx = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'users' AND indexname = 'idx_users_deleted_at'
            )
        """)
        print(f"  {'✅' if deleted_idx else '❌'} idx_users_deleted_at - индекс для soft delete")
        
        # Индекс для login_history
        login_idx = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'login_history' AND indexname = 'idx_login_history_user_id'
            )
        """)
        print(f"  {'✅' if login_idx else '❌'} idx_login_history_user_id - индекс истории входов")
        
        # Индекс для статуса проекта
        project_idx = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'projects' AND indexname = 'idx_projects_status'
            )
        """)
        print(f"  {'✅' if project_idx else '❌'} idx_projects_status - индекс статуса проекта")
        
        # Индекс для телефонов
        phone_idx = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'users' AND indexname = 'idx_users_phone_mobile'
            )
        """)
        print(f"  {'✅' if phone_idx else '❌'} idx_users_phone_mobile - индекс мобильного телефона")
        
        # Подсчёт записей
        print("\n📊 Статистика:")
        
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"  👥 Пользователей: {users_count}")
        
        active_users = await conn.fetchval("""
            SELECT COUNT(*) FROM users 
            WHERE deleted_at IS NULL AND blocked_at IS NULL
        """)
        print(f"  ✅ Активных пользователей: {active_users}")
        
        blocked_users = await conn.fetchval("""
            SELECT COUNT(*) FROM users 
            WHERE blocked_at IS NOT NULL AND deleted_at IS NULL
        """)
        print(f"  🔒 Заблокированных пользователей: {blocked_users}")
        
        deleted_users = await conn.fetchval("""
            SELECT COUNT(*) FROM users WHERE deleted_at IS NOT NULL
        """)
        print(f"  🗑️ Удалённых пользователей: {deleted_users}")
        
        roles_count = await conn.fetchval("SELECT COUNT(*) FROM roles")
        print(f"  🔐 Ролей: {roles_count}")
        
        projects_count = await conn.fetchval("SELECT COUNT(*) FROM projects")
        print(f"  📁 Проектов: {projects_count}")
        
        await conn.close()
        print("\n✅ Проверка структуры БД завершена")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(check_database())
