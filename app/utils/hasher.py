import bcrypt
import hashlib
import secrets

MAX_PASSWORD_LENGTH = 72

def truncate_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > MAX_PASSWORD_LENGTH:
        return pwd_bytes[:MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')
    return password

def hash_password(password: str) -> str:
    truncated = truncate_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(truncated.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return hash_password(password)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def verify_token_hash(token: str, hashed_token: str) -> bool:
    return hash_token(token) == hashed_token

def generate_random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)
