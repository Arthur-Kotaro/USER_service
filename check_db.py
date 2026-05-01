# check_db.py - расширенная проверка структуры PostgreSQL базы данных
from app.database import engine
from sqlalchemy import inspect, text
from sqlalchemy.engine.reflection import Inspector

def print_section(title: str, char: str = "=", width: int = 80):
    """Печать секции с заголовком"""
    print(f"\n{char * width}")
    print(f" {title} ".center(width, char))
    print(f"{char * width}")

def get_table_comment(inspector: Inspector, table_name: str) -> str:
    """Получить комментарий к таблице"""
    try:
        comments = inspector.get_table_comment(table_name)
        return comments.get('text', '') or ''
    except:
        return ''

def analyze_database():
    """Полный анализ структуры базы данных"""
    
    print_section("🔍 АНАЛИЗ СТРУКТУРЫ БАЗЫ ДАННЫХ", "=")
    
    # Проверка подключения
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n✅ Подключено: {version[:80]}...")
            
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"📚 База данных: {db_name}")
    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
        return
    
    # Получаем инспектор
    inspector = inspect(engine)
    
    # 1. Список всех таблиц
    print_section("📊 ТАБЛИЦЫ В БАЗЕ ДАННЫХ", "-")
    tables = inspector.get_table_names()
    
    for i, table in enumerate(tables, 1):
        comment = get_table_comment(inspector, table)
        comment_str = f" - {comment}" if comment else ""
        print(f"  {i:2}. {table}{comment_str}")
    
    # 2. Детальная информация по каждой таблице
    print_section("📋 ДЕТАЛЬНАЯ СТРУКТУРА ТАБЛИЦ", "-")
    
    for table in tables:
        print(f"\n📌 Таблица: {table}")
        print(f"   {'-' * 60}")
        
        # Колонки
        columns = inspector.get_columns(table)
        print(f"   🗂️ Колонки ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            comment = f" -- {col.get('comment', '')}" if col.get('comment') else ""
            print(f"      • {col['name']:25} {col['type']!s:20} {nullable}{default}{comment}")
        
        # Первичные ключи
        pk = inspector.get_pk_constraint(table)
        if pk.get('constrained_columns'):
            print(f"   🔑 Первичный ключ: {', '.join(pk['constrained_columns'])}")
        
        # Внешние ключи
        fks = inspector.get_foreign_keys(table)
        if fks:
            print(f"   🔗 Внешние ключи:")
            for fk in fks:
                print(f"      • {', '.join(fk['constrained_columns'])} → "
                      f"{fk['referred_table']}.{', '.join(fk['referred_columns'])} "
                      f"({fk.get('name', 'unnamed')})")
        
        # Индексы
        indexes = inspector.get_indexes(table)
        if indexes:
            print(f"   📇 Индексы:")
            for idx in indexes:
                unique = "UNIQUE " if idx['unique'] else ""
                condition = f" WHERE {idx.get('duplicate_constraint', '')}" if idx.get('duplicate_constraint') else ""
                print(f"      • {unique}INDEX {idx['name']} ON ({', '.join(idx['column_names'])}){condition}")
        
        # Проверка строк (для основных таблиц)
        if table in ['users', 'roles', 'projects', 'refresh_tokens', 'token_blacklist']:
            with engine.connect() as conn:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   📈 Количество записей: {count}")
                except Exception as e:
                    print(f"   ⚠️ Не удалось получить количество: {e}")
    
    # 3. Статистика по ключевым таблицам
    print_section("📈 СТАТИСТИКА", "-")
    
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
    
    with engine.connect() as conn:
        for label, query in stats_queries:
            try:
                result = conn.execute(text(query))
                count = result.scalar()
                print(f"   • {label:30}: {count}")
            except Exception as e:
                print(f"   • {label:30}: Ошибка - {e}")
    
    # 4. Схема связей (ER диаграмма в текстовом виде)
    print_section("🗺️ СХЕМА СВЯЗЕЙ (ER DIAGRAM)", "-")
    
    relationships = []
    for table in tables:
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            relationships.append({
                'from_table': table,
                'from_columns': fk['constrained_columns'],
                'to_table': fk['referred_table'],
                'to_columns': fk['referred_columns']
            })
    
    if relationships:
        print("\n   Связи между таблицами:\n")
        for rel in relationships:
            print(f"      {rel['from_table']}.{', '.join(rel['from_columns'])} → "
                  f"{rel['to_table']}.{', '.join(rel['to_columns'])}")
    
    # 5. Проверка констрейнтов
    print_section("⚙️ ПРОВЕРКА КОНСТРЕЙНТОВ", "-")
    
    constraint_checks = [
        ("Проверка email (users)", 
         "SELECT COUNT(*) FROM users WHERE email IS NOT NULL AND email != ''"),
        ("Проверка gender (users)", 
         "SELECT COUNT(*) FROM users WHERE gender IS NOT NULL AND gender NOT IN ('M', 'F')"),
        ("Проверка статусов (users)", 
         "SELECT COUNT(*) FROM users WHERE status NOT IN ('active', 'blocked', 'archived')"),
    ]
    
    with engine.connect() as conn:
        for label, query in constraint_checks:
            try:
                result = conn.execute(text(query))
                count = result.scalar()
                if label == "Проверка gender (users)" and count > 0:
                    print(f"   ⚠️ {label}: Некорректных записей - {count}")
                elif label == "Проверка статусов (users)" and count > 0:
                    print(f"   ⚠️ {label}: Некорректных записей - {count}")
                elif count == 0:
                    print(f"   ✅ {label}: OK")
                else:
                    print(f"   ℹ️ {label}: {count}")
            except Exception as e:
                print(f"   ⚠️ {label}: Ошибка - {e}")
    
    # 6. Информация о размере базы данных
    print_section("💾 ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ", "-")
    
    with engine.connect() as conn:
        try:
            # Размер базы данных
            result = conn.execute(text("""
                SELECT pg_database_size(current_database()) as size,
                       pg_size_pretty(pg_database_size(current_database())) as pretty_size
            """))
            row = result.fetchone()
            if row:
                print(f"   База данных: {row.pretty_size}")
            
            # Размер таблиц
            result = conn.execute(text("""
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 5
            """))
            
            print("\n   Самые большие таблицы:")
            for row in result:
                print(f"      • {row.tablename:25} {row.size}")
                
        except Exception as e:
            print(f"   ⚠️ {e}")
    
    print_section("✨ АНАЛИЗ ЗАВЕРШЕН", "=")

def check_user_model_compatibility():
    """Проверка совместимости модели User с существующей таблицей"""
    print_section("🔄 ПРОВЕРКА СОВМЕСТИМОСТИ МОДЕЛИ USER", "-")
    
    inspector = inspect(engine)
    db_columns = {col['name'] for col in inspector.get_columns('users')}
    
    # Поля из модели User (по рекомендации)
    expected_columns = {
        'user_id', 'user_name', 'password_hash', 'email', 'gender', 'birth_date',
        'dept_code', 'status', 'blocked_at', 'blocked_reason', 'blocked_by',
        'block_expires_at', 'created_at', 'updated_at', 'last_login_at'
    }
    
    missing_in_db = expected_columns - db_columns
    extra_in_db = db_columns - expected_columns
    
    if missing_in_db:
        print(f"\n   ⚠️ В БД отсутствуют поля (будут добавлены в модель?):")
        for col in missing_in_db:
            print(f"      - {col}")
    
    if extra_in_db:
        print(f"\n   ℹ️ В БД есть дополнительные поля (можно добавить в модель):")
        for col in extra_in_db:
            print(f"      - {col}")
    
    if not missing_in_db and not extra_in_db:
        print("\n   ✅ Модель User полностью совместима с БД")

if __name__ == "__main__":
    analyze_database()
    check_user_model_compatibility()
    
    print("\n💡 Совет: Для работы с БД используйте точные имена колонок из этой схемы")
