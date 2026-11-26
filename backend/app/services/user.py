import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import TokenClaims


class AccountDeletionError(Exception):
    """Supabase didn't delete the account; nothing was deleted."""


async def get_or_create_user(session: AsyncSession, claims: TokenClaims) -> User:
    """Return the user for a verified token, creating the row on their first request."""
    repo = UserRepository(session)
    user = await repo.get(claims.user_id)
    if user is None:
        try:
            user = await repo.add(User(id=claims.user_id, email=claims.email))
            await session.commit()
        except IntegrityError:
            # A concurrent first request created the row first; use theirs.
            await session.rollback()
            user = await repo.get(claims.user_id)
            assert user is not None
    elif claims.email and user.email != claims.email:
        user.email = claims.email
        await session.commit()
    return user


async def delete_user(session: AsyncSession, user: User, settings: Settings) -> None:
    """Delete the user's Supabase account, then their data here.

    Supabase goes first: if it fails, nothing is deleted and the user can retry.
    """
    if not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not set")
    key = settings.supabase_service_role_key
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user.id}",
                headers={"apikey": key, "Authorization": f"Bearer {key}"},
            )
        # 404 means it's already gone from Supabase; still clean up here.
        if resp.status_code != 404:
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise AccountDeletionError(str(e)) from e
    await UserRepository(session).delete(user)
    await session.commit()
