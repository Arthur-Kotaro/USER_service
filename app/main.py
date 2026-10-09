# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up User Service...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise
    yield
    print("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title="User Service",
    description="User Service",
    version="3.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "User Service is running", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


from app.api.v1 import auth, admin, users, internal, hr, departments

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(hr.router, prefix="/api/v1/hr", tags=["HR"])
app.include_router(departments.router, prefix="/api/v1", tags=["Departments"])
app.include_router(internal.router, prefix="/internal", tags=["Internal"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
