# app/utils/cleanup.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import asyncio
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.database import AsyncSessionLocal


async def cleanup_expired_tokens():
    """Периодическая очистка просроченных токенов и разблокировка"""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                blacklist_repo = BlacklistRepository(db)
                refresh_repo = RefreshTokenRepository(db)
                user_repo = UserRepository(db)

                # Удаляем просроченные токены из черного списка
                deleted_blacklist = await blacklist_repo.delete_expired()

                # Удаляем просроченные refresh токены
                deleted_refresh = await refresh_repo.delete_expired()

                # НОВОЕ: Автоматическая разблокировка пользователей с истекшей блокировкой
                unblocked = await user_repo.auto_unblock_expired()
                unlocked = await user_repo.auto_unlock_locked()

                if deleted_blacklist > 0 or deleted_refresh > 0 or unblocked > 0 or unlocked > 0:
                    print(f"Cleanup: deleted {deleted_blacklist} blacklisted tokens, "
                          f"{deleted_refresh} refresh tokens, "
                          f"unblocked {unblocked} users, "
                          f"unlocked {unlocked} users")

            # Ждем 1 час до следующей очистки
            await asyncio.sleep(3600)

        except Exception as e:
            print(f"Error in cleanup task: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)
