# scripts/create_super_admin.py
import asyncio
from app.database import AsyncSessionLocal
from app.repositories.user_repo import UserRepository
from app.utils.hasher import hash_password
from app.config import settings


async def create_super_admin():
    """Создание супер-админа"""
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)

        # Проверяем, существует ли уже супер-админ
        existing = await user_repo.get_by_username("super.admin")
        if existing:
            print("Super admin already exists!")
            return

        # Создаем супер-админа
        hashed_password = hash_password(settings.ADMIN_PASSWORD)
        user = await user_repo.create(
            email="super.admin@company.com",
            username="super.admin",
            hashed_password=hashed_password,
            full_name="Системный администратор",
            is_super_admin=True
        )

        # Назначаем роль admin
        from app.models.role import Role
        result = await db.execute(select(Role).where(Role.role_title == "admin"))
        admin_role = result.scalar_one_or_none()
        if admin_role:
            user.roles.append(admin_role)
            await db.commit()

        print(f"Super admin created: {user.user_name} (ID: {user.user_id})")
        print(f"Password: {settings.ADMIN_PASSWORD}")
        print("IMPORTANT: Change the password immediately after first login!")


if __name__ == "__main__":
    asyncio.run(create_super_admin())
