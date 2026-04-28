from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/userdb"
    
    # JWT
    SECRET_KEY: str  # должен быть длинным и случайным
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Администратор по умолчанию (создаётся при старте, если нет)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str  # задать в .env, при старте захэшируется
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
