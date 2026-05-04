#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/home/kotaro/code/IS_RE_engineering/USER_service')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.role import Role
from app.utils.hasher import hash_password
from app.config import settings

async def create_test_users():
    # Создаем engine
    engine = create_async_engine(settings.get_database_url, echo=True)
    
    # Создаем сессию
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Проверяем существование ролей
        admin_role = await session.get(Role, 1)
        if not admin_role:
            admin_role = Role(role_id=1, role_title="admin")
            session.add(admin_role)
        
        user_role = await session.get(Role, 2)
        if not user_role:
            user_role = Role(role_id=2, role_title="user")
            session.add(user_role)
        
        await session.commit()
        
        # Создаем администратора
        existing_admin = await session.execute(
            select(User).where(User.user_name == "admin")
        )
        if not existing_admin.scalar_one_or_none():
            admin = User(
                user_name="admin",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                status="active",
                password_updated_at=datetime.now(timezone.utc)
            )
            admin.roles.append(admin_role)
            session.add(admin)
            print("✓ Admin user created (login: admin@example.com, password: admin123)")
        
        # Создаем обычного пользователя
        existing_user = await session.execute(
            select(User).where(User.user_name == "user")
        )
        if not existing_user.scalar_one_or_none():
            user = User(
                user_name="user",
                email="user@example.com",
                password_hash=hash_password("user123"),
                status="active",
                password_updated_at=datetime.now(timezone.utc)
            )
            user.roles.append(user_role)
            session.add(user)
            print("✓ Regular user created (login: user@example.com, password: user123)")
        
        await session.commit()
        
        # Выводим список пользователей
        result = await session.execute(
            select(User).options(selectinload(User.roles))
        )
        users = result.scalars().all()
        
        print("\n=== Users in database ===")
        for u in users:
            roles = [r.role_title for r in u.roles]
            print(f"  - {u.user_name} ({u.email}): {', '.join(roles)}")
    
    await engine.dispose()

if __name__ == "__main__":
    from datetime import datetime, timezone
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    asyncio.run(create_test_users())
