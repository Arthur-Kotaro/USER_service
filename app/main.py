# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from app.database import engine
from app.utils.cleanup import cleanup_expired_tokens
from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    
    # Проверка подключения к БД
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise
    
    # Запускаем задачу очистки токенов
    task = asyncio.create_task(cleanup_expired_tokens())
    
    yield
    
    # Shutdown
    print("Shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Cleanup task cancelled")
    
    await engine.dispose()
    print("Database engine disposed")

# Создаем приложение с lifespan
app = FastAPI(
    title="User Service",
    version="1.0.0",
    lifespan=lifespan
)

# Эндпоинты
@app.get("/")
async def root():
    return {"message": "User Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Импорт и подключение роутеров
from app.api.v1 import auth, admin

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# Для отладки - вывести все роуты
print("\n=== Available routes ===")
for route in app.routes:
    methods = getattr(route, "methods", None)
    if methods:
        print(f"  {route.path} -> {methods}")
    else:
        print(f"  {route.path}")
print("=======================\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
