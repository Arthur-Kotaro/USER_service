# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.database import AsyncSessionLocal, engine
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
    
    # Создаем задачу очистки токенов без использования сессии в lifespan
    blacklist_repo = None
    refresh_repo = None
    task = None
    
    try:
        # Создаем репозитории внутри lifespan, но не держим сессию открытой
        async with AsyncSessionLocal() as db:
            blacklist_repo = BlacklistRepository(db)
            refresh_repo = RefreshTokenRepository(db)
            # Проверяем, что репозитории работают
            await blacklist_repo.delete_expired()
            await refresh_repo.delete_expired()
        
        # Запускаем задачу очистки, которая будет создавать свои сессии
        task = asyncio.create_task(cleanup_expired_tokens())
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise
    
    yield  # Приложение работает
    
    # Shutdown
    print("Shutting down...")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("Cleanup task cancelled")
    
    # Закрываем engine
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
