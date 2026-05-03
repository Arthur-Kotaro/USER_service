# tests/test_token_service.py
import pytest
from app.services.token_service import TokenService
from app.utils.hasher import hash_token

class TestTokenService:
    def test_create_access_token(self):
        token_service = TokenService()
        token = token_service.create_access_token({"user_id": 1, "email": "test@test.com"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        token_service = TokenService()
        token = token_service.create_refresh_token({"user_id": 1})
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_access_token_valid(self):
        token_service = TokenService()
        token = token_service.create_access_token({"user_id": 1, "email": "test@test.com"})
        
        payload = token_service.verify_access_token(token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["email"] == "test@test.com"
    
    def test_verify_access_token_invalid(self):
        token_service = TokenService()
        payload = token_service.verify_access_token("invalid.token.here")
        
        assert payload is None
    
    def test_verify_refresh_token_valid(self):
        token_service = TokenService()
        token = token_service.create_refresh_token({"user_id": 1})
        
        payload = token_service.verify_refresh_token(token)
        assert payload is not None
        assert payload["user_id"] == 1
    
    def test_token_hasher(self):
        token = "test_token_123"
        hashed = hash_token(token)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 длина
        assert hash_token(token) == hashed  # Детерминированность
