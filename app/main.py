from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.database import SessionLocal
from app.utils.cleanup import cleanup_expired_tokens

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    db = SessionLocal()
    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    task = asyncio.create_task(cleanup_expired_tokens(blacklist_repo, refresh_repo))
    
    yield  # Приложение работает
    
    # Shutdown
    print("Shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Cleanup task cancelled")
    db.close()

# Создаем приложение с lifespan
app = FastAPI(
    title="User Service",
    version="1.0.0",
    lifespan=lifespan
)

# Ваши эндпоинты
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
