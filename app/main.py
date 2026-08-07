# app/main.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from app.database import engine
from app.utils.cleanup import cleanup_expired_tokens
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
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
    
    # Запускаем фоновую задачу очистки токенов
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


# Создаём приложение с lifespan
app = FastAPI(
    title="User Service",
    description="""
    Сервис управления пользователями, ролями и аутентификацией.
    
    ## Возможности
    
    - Регистрация и аутентификация пользователей
    - Управление ролями (администратор, пользователь и др.)
    - Блокировка/разблокировка пользователей
    - Soft delete (восстановление удалённых пользователей)
    - Аудит действий и логирование входов
    - Управление проектами
    - Управление отделами (department)
    """,
    version="2.0.0",
    lifespan=lifespan
)


# ========== Базовые эндпоинты ==========

@app.get("/")
async def root():
    return {
        "message": "User Service is running",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "healthy"}


# ========== Импорт и подключение роутеров ==========

from app.api.v1 import auth, admin

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

# TODO: Подключить после создания
from app.api.v1 import users, projects
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])


# ========== Отладка: вывод всех роутов ==========

def print_routes():
    """Вывод всех зарегистрированных маршрутов (для отладки)"""
    print("\n=== Available routes ===")
    routes_info = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if methods:
            path = route.path
            methods_str = ", ".join(sorted(methods))
            routes_info.append(f"  {path} -> [{methods_str}]")
            print(routes_info[-1])
        elif hasattr(route, "path"):
            print(f"  {route.path} -> [GET] (static)")
        else:
            print(f"  {route}")
    
    print(f"Total routes: {len(routes_info)}")
    print("=======================\n")
    return routes_info


# Выводим маршруты при запуске (только если не в тестах)
if __name__ != "__main__":
    # Для production - выводим один раз при загрузке
    print_routes()


if __name__ == "__main__":
    import uvicorn
    
    # При прямом запуске выводим маршруты для отладки
    print_routes()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
