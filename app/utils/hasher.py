# app/utils/hasher.py
from passlib.context import CryptContext
import hashlib
import secrets

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === Функции для работы с паролями ===
def hash_password(password: str) -> str:
    """Хеширует пароль с использованием bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля его хешу"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Алиас для hash_password"""
    return hash_password(password)

# === Функции для работы с токенами ===
def hash_token(token: str) -> str:
    """
    Хеширует токен с использованием sha256.
    Используется для хранения токенов в черном списке.
    
    Args:
        token: Токен для хеширования
        
    Returns:
        str: SHA256 хеш токена
    """
    return hashlib.sha256(token.encode()).hexdigest()

def verify_token_hash(token: str, hashed_token: str) -> bool:
    """
    Проверяет соответствие токена его хешу
    
    Args:
        token: Обычный токен
        hashed_token: Хешированный токен для сравнения
        
    Returns:
        bool: True если хеши совпадают
    """
    return hash_token(token) == hashed_token

# === Вспомогательные функции ===
def generate_random_token(length: int = 32) -> str:
    """Генерирует случайный токен для refresh token"""
    return secrets.token_urlsafe(length)

def generate_reset_token() -> str:
    """Генерирует токен для сброса пароля"""
    return secrets.token_urlsafe(32)
