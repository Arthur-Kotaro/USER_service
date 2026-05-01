# app/repositories/user_repo.py
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from typing import Optional, List
from app.models.user import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return self.db.query(User).filter(User.email == email).first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        return self.db.query(User).filter(User.username == username).first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить список пользователей с пагинацией"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    async def create(self, email: str, username: str, hashed_password: str) -> User:
        """Создать нового пользователя"""
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def update(self, user_id: int, update_data: dict) -> Optional[User]:
        """Обновить данные пользователя"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        """Удалить пользователя"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    async def update_last_login(self, user_id: int) -> None:
        """Обновить время последнего входа"""
        user = await self.get_by_id(user_id)
        if user:
            from datetime import datetime
            user.last_login = datetime.utcnow()
            self.db.commit()
