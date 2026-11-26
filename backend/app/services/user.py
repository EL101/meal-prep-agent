import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import TokenClaims


class AccountDeletionError(Exception):
    """Local data was deleted but Supabase didn't delete the account. Safe to retry."""


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
    return user


async def delete_user(session: AsyncSession, user: User, settings: Settings) -> None:
    """Delete the user's data here, then their Supabase account.

    Local data goes first so it can never outlive the account. If the Supabase call then
    fails (or times out), the account may still exist; if so, the user can sign in and retry.
    """
    if not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_SECRET_KEY is not set")
    user_id = user.id
    await UserRepository(session).delete(user)
    await session.commit()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}",
                # Secret keys aren't JWTs: Supabase wants them on `apikey` only, not as a Bearer.
                headers={"apikey": settings.supabase_secret_key},
            )
        # 404 means it's already gone from Supabase, which is the outcome we want.
        if resp.status_code != 404:
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise AccountDeletionError(str(e)) from e
