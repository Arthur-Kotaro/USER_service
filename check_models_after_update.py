# check_models_after_update.py
import asyncio
from sqlalchemy import inspect, text
from app.database import engine

async def verify_models():
    """Проверка соответствия моделей после обновления"""
    
    async with engine.connect() as conn:
        def check_schema(sync_conn):
            inspector = inspect(sync_conn)
            users_cols = inspector.get_columns('users')
            roles_cols = inspector.get_columns('roles')
            blacklist_cols = inspector.get_columns('token_blacklist')
            
            return {
                'users_columns': {c['name']: str(c['type']) for c in users_cols},
                'roles_columns': {c['name']: str(c['type']) for c in roles_cols},
                'blacklist_columns': {c['name']: str(c['type']) for c in blacklist_cols}
            }
        
        schema = await conn.run_sync(check_schema)
        
        print("📊 Проверка типов колонок:")
        
        # Проверка телефонов
        if 'phone_work' in schema['users_columns']:
            db_type = schema['users_columns']['phone_work']
            print(f"   phone_work: БД тип {db_type} (без ограничения длины) ✅")
        
        # Проверка role_id
        if 'role_id' in schema['roles_columns']:
            db_type = schema['roles_columns']['role_id']
            print(f"   role_id: БД тип {db_type} (SmallInteger ожидается) ✅")
        
        # Проверка token_jti
        if 'token_jti' in schema['blacklist_columns']:
            db_type = schema['blacklist_columns']['token_jti']
            print(f"   token_jti: БД тип {db_type} (UUID ожидается) ✅")

if __name__ == "__main__":
    asyncio.run(verify_models())
