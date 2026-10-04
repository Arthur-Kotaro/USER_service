# app/services/impersonation_service.py
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
import httpx
from app.config import settings
from app.utils.redis_client import redis_client


class ImpersonationService:
    def __init__(self, user_repo, refresh_repo, user_service_url: str):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo
        self.user_service_url = user_service_url

    async def _is_direct_subordinate(self, manager_id: int, subordinate_id: int) -> bool:
        sub = await self.user_repo.get_by_id(subordinate_id, include_deleted=False)
        if not sub:
            return False
        return sub.head_id == manager_id

    async def _has_delegation(self, delegate_id: int, delegator_id: int) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"http://localhost:8011/api/v1/delegations/check",
                    params={"delegate_id": delegate_id, "delegator_id": delegator_id},
                )
                if resp.status_code == 200:
                    return resp.json().get("has_delegation", False)
        except Exception:
            return False
        return False

    async def impersonate(
        self,
        recipient_id: int,
        donor_id: int,
        ttl_hours: int = 2,
    ) -> dict:
        donor = await self.user_repo.get_by_id(donor_id, include_deleted=True)
        if not donor:
            raise HTTPException(404, "Donor not found")
        if donor.deleted_at is not None:
            raise HTTPException(400, "Donor is deleted")
        if donor.blocked_at is not None:
            raise HTTPException(400, "Donor is blocked")

        allowed = False
        if await self._is_direct_subordinate(recipient_id, donor_id):
            allowed = True
        elif await self._has_delegation(delegate_id=recipient_id, delegator_id=donor_id):
            allowed = True

        if not allowed:
            raise HTTPException(403, "No right to impersonate this user")

        impersonation_id = str(uuid.uuid4())
        exp = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

        payload = {
            "user_id": donor.user_id,
            "roles": donor.get_roles_titles(),
            "is_super_admin": bool(donor.is_super_admin),
            "impersonated_by": recipient_id,
            "impersonation_id": impersonation_id,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": exp,
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        await redis_client.set(
            f"impersonation:{impersonation_id}",
            str(recipient_id),
            ex=ttl_hours * 3600,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "impersonation_id": impersonation_id,
            "recipient_id": recipient_id,
            "donor_id": donor_id,
            "expires_in": ttl_hours * 3600,
        }

    async def close(self, impersonation_id: str) -> bool:
        key = f"impersonation:{impersonation_id}"
        exists = await redis_client.exists(key)
        if exists:
            await redis_client.delete(key)
        return bool(exists)
