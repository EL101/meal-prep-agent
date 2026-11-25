import uuid
from functools import lru_cache
from typing import Annotated

import jwt
from arq.connections import ArqRedis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session

bearer = HTTPBearer(auto_error=False)


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{get_settings().supabase_url}/auth/v1/.well-known/jwks.json")


def _decode(token: str) -> dict[str, object]:
    s = get_settings()
    if s.supabase_jwt_secret:  # legacy HS256 projects
        return jwt.decode(
            token, s.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated"
        )
    key = _jwks_client().get_signing_key_from_jwt(token)  # asymmetric signing keys
    return jwt.decode(token, key.key, algorithms=["ES256", "RS256"], audience="authenticated")


async def current_user_id(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> uuid.UUID:
    """Verify the Supabase access token the mobile app sends and return the user's id."""
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    try:
        claims = _decode(creds.credentials)
        return uuid.UUID(str(claims["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc


def get_queue(request: Request) -> ArqRedis:
    return request.app.state.queue  # type: ignore[no-any-return]


UserId = Annotated[uuid.UUID, Depends(current_user_id)]
Session = Annotated[AsyncSession, Depends(get_session)]
Queue = Annotated[ArqRedis, Depends(get_queue)]
