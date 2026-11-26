import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_token_verifier
from app.config import Settings, get_settings
from app.db import Base, get_session
from app.main import app
from app.services.auth import SupabaseTokenVerifier

SUPABASE_URL = "https://test.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"

_signing_key = ec.generate_private_key(ec.SECP256R1())


@dataclass
class _Key:
    key: object


class FakeJWKSClient:
    """Stands in for PyJWKClient: always returns the test signing key's public half."""

    def get_signing_key_from_jwt(self, token: str) -> _Key:
        return _Key(_signing_key.public_key())


def make_token(
    sub: uuid.UUID | str | None = None,
    email: str | None = "cook@example.com",
    key=_signing_key,
    **overrides,
) -> str:
    claims = {
        "sub": str(sub or uuid.uuid4()),
        "email": email,
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 3600,
        **overrides,
    }
    return jwt.encode(claims, key, algorithm="ES256")


@pytest.fixture
def settings() -> Settings:
    return Settings(supabase_url=SUPABASE_URL, supabase_secret_key="sb_secret_test")


@pytest.fixture
def verifier(settings: Settings) -> SupabaseTokenVerifier:
    return SupabaseTokenVerifier(settings, jwks_client=FakeJWKSClient())


@pytest.fixture
def client(settings: Settings, verifier: SupabaseTokenVerifier) -> Iterator[TestClient]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def override_session():
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    with TestClient(app) as c:
        c.portal.call(create_tables)
        c.sessionmaker = sessionmaker  # lets tests look at the database directly
        yield c
        c.portal.call(engine.dispose)
    app.dependency_overrides.clear()
