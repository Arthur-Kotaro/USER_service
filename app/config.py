# app/config.py
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    # Режим работы
    ENVIRONMENT: str = "development"  # development | staging | production

    # PostgreSQL настройки
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str  # ❌ Убрал значение по умолчанию!
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "user_service"
    DATABASE_URL: Optional[str] = None

    # JWT настройки
    SECRET_KEY: str  # ❌ Убрал значение по умолчанию!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # ⬅️ Уменьшил с 30 до 15 (безопаснее)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin
    ADMIN_PASSWORD: str  # ❌ Убрал значение по умолчанию!

    # Email настройки
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def is_debug(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @field_validator('SECRET_KEY')
    def check_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v

    @field_validator('ADMIN_PASSWORD')
    def check_admin_password(cls, v):
        if len(v) < 12:
            raise ValueError('ADMIN_PASSWORD must be at least 12 characters')
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
