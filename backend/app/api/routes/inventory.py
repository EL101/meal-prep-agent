import uuid
from typing import Literal

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import Queue, Session, UserId
from app.api.routes.profile import get_or_create_profile
from app.models import InventoryItem
from app.schemas.api import InventoryItemIn, InventoryItemOut, JobAccepted
from app.services import storage

router = APIRouter(prefix="/inventory", tags=["inventory"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.get("", response_model=list[InventoryItemOut])
async def list_inventory(user_id: UserId, session: Session) -> list[InventoryItem]:
    rows = await session.scalars(
        select(InventoryItem)
        .where(InventoryItem.user_id == user_id)
        .order_by(InventoryItem.expires_on.asc().nulls_last())
    )
    return list(rows)


@router.post("", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
async def add_item(body: InventoryItemIn, user_id: UserId, session: Session) -> InventoryItem:
    await get_or_create_profile(session, user_id)
    item = InventoryItem(user_id=user_id, source="manual", **body.model_dump())
    session.add(item)
    await session.commit()
    return item


@router.post("/{item_id}/confirm", response_model=InventoryItemOut)
async def confirm_item(
    item_id: uuid.UUID, body: InventoryItemIn, user_id: UserId, session: Session
) -> InventoryItem:
    """User confirms (and optionally corrects) an item Claude wasn't sure about."""
    item = await session.get(InventoryItem, item_id)
    if item is None or item.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    for field, value in body.model_dump().items():
        setattr(item, field, value)
    item.needs_confirmation, item.confidence = False, 1.0
    await session.commit()
    return item


@router.post("/scan", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def scan_image(
    file: UploadFile,
    kind: Literal["fridge", "pantry", "receipt"] = Form(),
    *,
    user_id: UserId,
    session: Session,
    queue: Queue,
) -> JobAccepted:
    """Store the photo, then let the worker ask Claude to read it."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a JPEG/PNG/WebP/GIF")
    await get_or_create_profile(session, user_id)
    job_id = uuid.uuid4()
    path = await storage.upload_image(
        f"{user_id}/{job_id}-{kind}", await file.read(), file.content_type
    )
    await queue.enqueue_job(
        "scan_inventory", str(user_id), path, file.content_type, kind, _job_id=str(job_id)
    )
    return JobAccepted(id=job_id, status="queued")
