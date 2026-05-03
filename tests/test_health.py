# tests/test_health.py
from fastapi import status

class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "User Service" in response.json()["message"]
    
    def test_docs_available(self, client):
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    def test_openapi_schema(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        assert "openapi" in response.json()
