# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.role import Role
from app.utils.hasher import hash_password

# Тестовая база данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db?check_same_thread=False"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    return TestClient(app)

@pytest.fixture
def test_admin(db):
    admin = User(
        user_name="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        status="active"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture
def test_user(db):
    user = User(
        user_name="testuser",
        email="test@test.com",
        password_hash=hash_password("test123"),
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_token(client, test_admin):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "admin123"}
    )
    return response.json()["access_token"]

@pytest.fixture
def user_token(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "test123"}
    )
    return response.json()["access_token"]
