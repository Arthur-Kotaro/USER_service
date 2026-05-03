# tests/test_user_service.py
import pytest
from app.services.user_service import UserService
from app.services.admin_service import AdminService
from app.schemas.admin import UserCreateAdmin

class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user(self, db):
        admin_service = AdminService(db)
        user_data = UserCreateAdmin(
            user_name="testservice",
            email="service@test.com",
            password="testpass",
            status="active"
        )
        
        user = await admin_service.create_user(user_data)
        assert user.user_name == "testservice"
        assert user.email == "service@test.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db, test_user):
        admin_service = AdminService(db)
        user = await admin_service.get_user_by_id(test_user.user_id)
        assert user is not None
        assert user.user_id == test_user.user_id
    
    @pytest.mark.asyncio
    async def test_update_user(self, db, test_user):
        admin_service = AdminService(db)
        from app.schemas.admin import UserUpdateAdmin
        
        update_data = UserUpdateAdmin(email="updated_service@test.com")
        user = await admin_service.update_user(test_user.user_id, update_data)
        
        assert user is not None
        assert user.email == "updated_service@test.com"
    
    @pytest.mark.asyncio
    async def test_block_user(self, db, test_user, test_admin):
        admin_service = AdminService(db)
        
        user = await admin_service.block_user(
            test_user.user_id,
            test_admin.user_id,
            "Test block reason"
        )
        
        assert user is not None
        assert user.status == "blocked"
        assert user.blocked_reason == "Test block reason"
    
    @pytest.mark.asyncio
    async def test_unblock_user(self, db, test_user, test_admin):
        admin_service = AdminService(db)
        
        # Блокируем
        await admin_service.block_user(test_user.user_id, test_admin.user_id, "Test")
        
        # Разблокируем
        user = await admin_service.unblock_user(test_user.user_id)
        
        assert user is not None
        assert user.status == "active"
        assert user.blocked_at is None
