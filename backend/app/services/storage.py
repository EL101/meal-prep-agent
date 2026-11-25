"""Supabase Storage for fridge/pantry/receipt photos. Server-side only (service role key)."""

from supabase import AsyncClient, acreate_client

from app.config import get_settings

_client: AsyncClient | None = None


async def _get_client() -> AsyncClient:
    global _client
    if _client is None:
        s = get_settings()
        _client = await acreate_client(s.supabase_url, s.supabase_service_role_key)
    return _client


async def upload_image(path: str, data: bytes, content_type: str) -> str:
    client = await _get_client()
    bucket = get_settings().supabase_storage_bucket
    await client.storage.from_(bucket).upload(path, data, {"content-type": content_type})
    return path


async def download_image(path: str) -> bytes:
    client = await _get_client()
    return await client.storage.from_(get_settings().supabase_storage_bucket).download(path)
