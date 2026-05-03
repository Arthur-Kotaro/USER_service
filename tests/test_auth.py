# tests/test_auth.py
import pytest
from fastapi import status

class TestAuth:
    def test_login_success(self, client, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test123"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
    
    def test_login_wrong_password(self, client, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "wrong"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "test123"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_register_user_success(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "user_name": "newuser",
                "email": "new@test.com",
                "password": "new123",
                "confirm_password": "new123"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "user_id" in response.json()
    
    def test_register_duplicate_username(self, client, test_user):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "user_name": "testuser",
                "email": "another@test.com",
                "password": "test123",
                "confirm_password": "test123"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_passwords_mismatch(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "user_name": "newuser2",
                "email": "new2@test.com",
                "password": "test123",
                "confirm_password": "test456"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_refresh_token(self, client, test_user):
        # Сначала получаем токены
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Обновляем токен
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
