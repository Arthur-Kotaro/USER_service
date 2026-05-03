# check_db_tables.py
from app.database import engine, Base
from app.models import User, Role, Project, Department, RefreshToken, TokenBlacklist
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print("Existing tables:", tables)

# Проверим, есть ли таблица departament
if 'departament' in tables:
    print("Table 'departament' exists")
    columns = inspector.get_columns('departament')
    print("Columns:", [col['name'] for col in columns])
