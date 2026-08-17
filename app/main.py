# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from app.database import engine
from app.utils.cleanup import cleanup_expired_tokens
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise
    task = asyncio.create_task(cleanup_expired_tokens())
    yield
    print("Shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Cleanup task cancelled")
    await engine.dispose()
    print("Database engine disposed")


app = FastAPI(
    title="User Service",
    description="User Service",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "message": "User Service is running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ========== Импорт и регистрация роутеров ==========
from app.api.v1 import auth, admin, users

# ВАЖНО: добавляем префиксы в main.py, а не в роутерах
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


def print_routes():
    print("\n=== Available routes ===")
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if methods:
            print(f"  {route.path} -> [{', '.join(sorted(methods))}]")
    print("=======================\n")


if __name__ != "__main__":
    print_routes()


if __name__ == "__main__":
    import uvicorn
    print_routes()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
