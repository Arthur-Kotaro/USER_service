# tests/test_admin.py
import pytest
from fastapi import status

class TestAdmin:
    def test_create_user_by_admin(self, client, admin_token):
        response = client.post(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "user_name": "newuser_by_admin",
                "email": "newadmin@test.com",
                "password": "adminpass",
                "status": "active"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["user_name"] == "newuser_by_admin"
    
    def test_create_user_unauthorized(self, client, user_token):
        response = client.post(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "user_name": "hacker",
                "email": "hacker@test.com",
                "password": "hack123",
                "status": "active"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_all_users_admin(self, client, admin_token):
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "users" in response.json()
        assert "total" in response.json()
    
    def test_get_user_by_id(self, client, admin_token, test_user):
        response = client.get(
            f"/api/v1/admin/users/{test_user.user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_name"] == test_user.user_name
    
    def test_update_user(self, client, admin_token, test_user):
        response = client.put(
            f"/api/v1/admin/users/{test_user.user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": "updated@test.com"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "updated@test.com"
    
    def test_block_user(self, client, admin_token, test_user):
        response = client.post(
            f"/api/v1/admin/users/{test_user.user_id}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test block", "expires_at": None}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "blocked successfully" in response.json()["message"]
    
    def test_block_self_admin(self, client, admin_token, test_admin):
        response = client.post(
            f"/api/v1/admin/users/{test_admin.user_id}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Cannot block self"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unblock_user(self, client, admin_token, test_user):
        # Сначала блокируем
        client.post(
            f"/api/v1/admin/users/{test_user.user_id}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test block"}
        )
        
        # Разблокируем
        response = client.post(
            f"/api/v1/admin/users/{test_user.user_id}/unblock",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "unblocked successfully" in response.json()["message"]
    
    def test_delete_user(self, client, admin_token, test_user):
        response = client.delete(
            f"/api/v1/admin/users/{test_user.user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_self_admin(self, client, admin_token, test_admin):
        response = client.delete(
            f"/api/v1/admin/users/{test_admin.user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_admin_stats(self, client, admin_token):
        response = client.get(
            "/api/v1/admin/stats/overview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "total_users" in response.json()
        assert "active_users" in response.json()
