# app/utils/cleanup.py
import asyncio
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.database import AsyncSessionLocal

async def cleanup_expired_tokens():
    """Периодическая очистка просроченных токенов"""
    while True:
        try:
            # Создаем новую сессию для каждой очистки
            async with AsyncSessionLocal() as db:
                blacklist_repo = BlacklistRepository(db)
                refresh_repo = RefreshTokenRepository(db)
                
                # Удаляем просроченные токены из черного списка
                deleted_blacklist = await blacklist_repo.delete_expired()
                
                # Удаляем просроченные refresh токены
                deleted_refresh = await refresh_repo.delete_expired()
                
                if deleted_blacklist > 0 or deleted_refresh > 0:
                    print(f"Cleanup: deleted {deleted_blacklist} blacklisted tokens and {deleted_refresh} refresh tokens")
            
            # Ждем 1 час до следующей очистки
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"Error in cleanup task: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)  # При ошибке ждем минуту и пробуем снова
