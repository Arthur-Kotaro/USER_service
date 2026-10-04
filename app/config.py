# app/config.py
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "user_service"
    DATABASE_URL: Optional[str] = None

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_BLACKLIST_DB: int = 0

    USER_SERVICE_URL: str = "http://localhost:8000"
    DELEGATION_SERVICE_URL: str = "http://localhost:8011"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8012"

    ADMIN_PASSWORD: str
    INTERNAL_API_KEY: str

    SMTP_HOST: str = "smtp.yandex.com"
    SMTP_PORT: int = 465
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

    @field_validator("SECRET_KEY")
    def check_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("ADMIN_PASSWORD")
    def check_admin_password(cls, v):
        if len(v) < 12:
            raise ValueError("ADMIN_PASSWORD must be at least 12 characters")
        return v

    class Config:
        env_file = (".env", "../.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
