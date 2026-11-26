"""Verifies Supabase access tokens.

Supabase signs access tokens with the project's asymmetric signing key; we check them against
the project's public JWKS, so the backend holds no JWT secret.
"""

import uuid
from dataclasses import dataclass

import jwt
from fastapi.concurrency import run_in_threadpool

from app.config import Settings


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    email: str | None


class SupabaseTokenVerifier:
    def __init__(self, settings: Settings, jwks_client: jwt.PyJWKClient | None = None) -> None:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL is not set")
        base = settings.supabase_url.rstrip("/")
        self.issuer = f"{base}/auth/v1"
        self.audience = settings.supabase_jwt_audience
        # PyJWKClient caches keys and refetches when it sees an unknown `kid` (key rotation).
        self.jwks_client = jwks_client or jwt.PyJWKClient(
            f"{self.issuer}/.well-known/jwks.json", cache_keys=True
        )

    async def verify(self, token: str) -> TokenClaims:
        try:
            # The JWKS fetch is blocking I/O; keep it off the event loop.
            key = await run_in_threadpool(self.jwks_client.get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["ES256", "RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
            user_id = uuid.UUID(claims["sub"])
        except (jwt.PyJWTError, ValueError) as e:
            raise InvalidTokenError(str(e)) from e
        return TokenClaims(user_id=user_id, email=claims.get("email"))
