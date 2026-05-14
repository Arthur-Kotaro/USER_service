# check_db_tables.py - Асинхронная версия
import asyncio
from sqlalchemy import inspect, text
from app.database import engine

async def check_tables():
    """Асинхронная проверка таблиц в базе данных"""
    
    async with engine.connect() as conn:
        # Выполняем инспекцию через run_sync
        def get_tables(sync_conn):
            inspector = inspect(sync_conn)
            return inspector.get_table_names()
        
        tables = await conn.run_sync(get_tables)
        print("📊 Существующие таблицы:", tables)
        
        # Проверим, есть ли таблица departament
        if 'departament' in tables:
            print("\n✅ Таблица 'departament' существует")
            
            # Получаем колонки таблицы
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_columns('departament')
            
            columns = await conn.run_sync(get_columns)
            print("📋 Колонки:", [col['name'] for col in columns])
            
            # Дополнительная информация
            print("\n📌 Детальная структура departament:")
            for col in columns:
                print(f"   • {col['name']:20} {str(col['type']):25} nullable={col['nullable']}")
        else:
            print("\n❌ Таблица 'departament' не найдена")

async def check_all_tables_detailed():
    """Детальная проверка всех таблиц"""
    
    async with engine.connect() as conn:
        def get_all_info(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            result = {}
            
            for table in tables:
                columns = inspector.get_columns(table)
                pk = inspector.get_pk_constraint(table)
                fks = inspector.get_foreign_keys(table)
                
                result[table] = {
                    'columns': [{'name': col['name'], 'type': str(col['type']), 'nullable': col['nullable']} for col in columns],
                    'primary_key': pk.get('constrained_columns', []),
                    'foreign_keys': [(fk['constrained_columns'], fk['referred_table'], fk['referred_columns']) for fk in fks]
                }
            
            return result
        
        all_info = await conn.run_sync(get_all_info)
        
        print("\n" + "="*80)
        print("📊 ДЕТАЛЬНАЯ СТРУКТУРА ВСЕХ ТАБЛИЦ")
        print("="*80)
        
        for table_name, info in all_info.items():
            print(f"\n📌 Таблица: {table_name}")
            print(f"   Колонки ({len(info['columns'])}):")
            for col in info['columns']:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"      • {col['name']:25} {col['type']:30} {nullable}")
            
            if info['primary_key']:
                print(f"   🔑 Первичный ключ: {', '.join(info['primary_key'])}")
            
            if info['foreign_keys']:
                print(f"   🔗 Внешние ключи:")
                for fk in info['foreign_keys']:
                    print(f"      • {', '.join(fk[0])} → {fk[1]}.{', '.join(fk[2])}")

if __name__ == "__main__":
    async def main():
        await check_tables()
        await check_all_tables_detailed()
    
    asyncio.run(main())
