# app/utils/cleanup.py
import asyncio
import logging
from datetime import datetime
from typing import Optional
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository

logger = logging.getLogger(__name__)

async def cleanup_expired_tokens(
    blacklist_repo: Optional[BlacklistRepository] = None,
    refresh_repo: Optional[RefreshTokenRepository] = None,
    interval_seconds: int = 3600  # 1 час по умолчанию
):
    """
    Фоновая задача для очистки просроченных токенов
    
    Args:
        blacklist_repo: Репозиторий черного списка
        refresh_repo: Репозиторий refresh токенов
        interval_seconds: Интервал между очистками в секундах
    """
    if not blacklist_repo or not refresh_repo:
        logger.warning("Cleanup task started without required repositories")
        return
    
    logger.info(f"Cleanup task started. Interval: {interval_seconds} seconds")
    
    while True:
        try:
            # Очистка черного списка токенов
            deleted_blacklist = await blacklist_repo.delete_expired()
            
            # Очистка просроченных refresh токенов
            deleted_refresh = await refresh_repo.delete_expired()
            
            if deleted_blacklist > 0 or deleted_refresh > 0:
                logger.info(
                    f"Cleanup completed: {deleted_blacklist} blacklisted tokens, "
                    f"{deleted_refresh} refresh tokens deleted at {datetime.utcnow()}"
                )
            else:
                logger.debug(f"Cleanup completed: no expired tokens found at {datetime.utcnow()}")
                
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)
        
        # Ждем перед следующим запуском
        await asyncio.sleep(interval_seconds)

async def cleanup_resources():
    """
    Очистка ресурсов при завершении работы приложения
    """
    logger.info("Cleaning up resources before shutdown...")
    # Добавьте здесь код закрытия соединений, если нужно
    await asyncio.sleep(0.1)  # Даем время на завершение
    logger.info("Cleanup completed")

# Для тестирования
if __name__ == "__main__":
    async def test():
        print("Testing cleanup function...")
        # Здесь можно добавить тестовый код
        print("Test completed")
    
    asyncio.run(test())
