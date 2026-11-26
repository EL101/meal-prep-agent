import time
import uuid

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.models.user import User
from app.services import user as user_service
from tests.conftest import SUPABASE_URL, make_token

_RealAsyncClient = httpx.AsyncClient


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_requires_token(client):
    resp = client.get("/me")
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        make_token(exp=int(time.time()) - 10),
        make_token(aud="anon"),
        make_token(iss="https://other.supabase.co/auth/v1"),
        make_token(key=ec.generate_private_key(ec.SECP256R1())),
        make_token(sub="not-a-uuid"),
    ],
    ids=["garbage", "expired", "wrong-aud", "wrong-iss", "wrong-key", "bad-sub"],
)
def test_me_rejects_bad_tokens(client, token):
    assert client.get("/me", headers=auth(token)).status_code == 401


def test_first_request_creates_user_then_reuses_it(client):
    user_id = uuid.uuid4()
    token = make_token(sub=user_id)
    first = client.get("/me", headers=auth(token))
    assert first.status_code == 200
    assert first.json()["id"] == str(user_id)
    assert first.json()["email"] == "cook@example.com"

    assert client.get("/me", headers=auth(token)).json() == first.json()


def test_apple_private_relay_user_without_email(client):
    resp = client.get("/me", headers=auth(make_token(email=None)))
    assert resp.status_code == 200
    assert resp.json()["email"] is None


def _user_exists(client, user_id: uuid.UUID) -> bool:
    async def check() -> bool:
        async with client.sessionmaker() as session:
            return await session.get(User, user_id) is not None

    return client.portal.call(check)


def _mock_supabase(monkeypatch, status_code: int) -> list[httpx.Request]:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(status_code)

    monkeypatch.setattr(
        user_service.httpx,
        "AsyncClient",
        lambda **kw: _RealAsyncClient(transport=httpx.MockTransport(handler), **kw),
    )
    return calls


def test_delete_me_removes_supabase_account_and_local_row(client, monkeypatch):
    calls = _mock_supabase(monkeypatch, 200)
    user_id = uuid.uuid4()
    token = make_token(sub=user_id)
    client.get("/me", headers=auth(token))
    assert _user_exists(client, user_id)

    assert client.delete("/me", headers=auth(token)).status_code == 204
    assert str(calls[0].url) == f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
    assert calls[0].headers["Authorization"] == "Bearer service-key"
    assert not _user_exists(client, user_id)


def test_delete_me_cleans_up_when_supabase_account_already_gone(client, monkeypatch):
    _mock_supabase(monkeypatch, 404)
    user_id = uuid.uuid4()
    token = make_token(sub=user_id)
    client.get("/me", headers=auth(token))

    assert client.delete("/me", headers=auth(token)).status_code == 204
    assert not _user_exists(client, user_id)


def test_delete_me_removes_local_data_even_when_supabase_fails(client, monkeypatch):
    calls = _mock_supabase(monkeypatch, 500)
    user_id = uuid.uuid4()
    token = make_token(sub=user_id)
    client.get("/me", headers=auth(token))

    assert client.delete("/me", headers=auth(token)).status_code == 502
    assert not _user_exists(client, user_id)

    # The Supabase account still exists, so a retry goes through.
    _mock_supabase(monkeypatch, 200)
    assert client.delete("/me", headers=auth(token)).status_code == 204
    assert len(calls) == 1
