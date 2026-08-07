# app/repositories/login_history_repo.py (НОВЫЙ ФАЙЛ)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from datetime import datetime, timezone
from app.models.login_history import LoginHistory


class LoginHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: Optional[int],
        login_status: str,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> LoginHistory:
        """Создание записи о попытке входа"""
        login_history = LoginHistory(
            user_id=user_id,
            login_status=login_status,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        self.db.add(login_history)
        await self.db.commit()
        await self.db.refresh(login_history)
        return login_history
    
    async def get_by_user(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[LoginHistory]:
        """Получение истории входов пользователя"""
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)
        
        if status:
            query = query.where(LoginHistory.login_status == status)
        
        query = query.order_by(desc(LoginHistory.login_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_last_login(self, user_id: int) -> Optional[LoginHistory]:
        """Получение последнего успешного входа пользователя"""
        result = await self.db.execute(
            select(LoginHistory)
            .where(
                LoginHistory.user_id == user_id,
                LoginHistory.login_status == "success"
            )
            .order_by(desc(LoginHistory.login_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_failed_attempts_count(
        self, 
        user_id: int, 
        since: Optional[datetime] = None
    ) -> int:
        """Количество неудачных попыток входа"""
        query = select(LoginHistory).where(
            LoginHistory.user_id == user_id,
            LoginHistory.login_status == "failed"
        )
        
        if since:
            query = query.where(LoginHistory.login_at >= since)
        else:
            # По умолчанию за последние 24 часа
            since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.where(LoginHistory.login_at >= since)
        
        result = await self.db.execute(query)
        return len(result.scalars().all())
    
    async def delete_old(self, days: int = 90) -> int:
        """Удаление старых записей (старше days дней)"""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(LoginHistory).where(LoginHistory.login_at <= cutoff)
        )
        old_records = result.scalars().all()
        
        for record in old_records:
            await self.db.delete(record)
        
        await self.db.commit()
        return len(old_records)
