async def cleanup_expired_tokens(blacklist_repo, refresh_repo):
    while True:
        await asyncio.sleep(3600)  # каждый час
        await blacklist_repo.delete_expired()
        await refresh_repo.delete_expired()
