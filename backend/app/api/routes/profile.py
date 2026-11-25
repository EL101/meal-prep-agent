import uuid

from fastapi import APIRouter, status
from sqlalchemy import delete, select

from app.api.deps import Session, UserId
from app.models import ExcludedFood, Profile
from app.schemas.api import ExcludedFoodIn, ExcludedFoodOut, ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


async def get_or_create_profile(session: Session, user_id: uuid.UUID) -> Profile:
    profile = await session.get(Profile, user_id)
    if profile is None:
        profile = Profile(user_id=user_id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
async def read_profile(user_id: UserId, session: Session) -> Profile:
    return await get_or_create_profile(session, user_id)


@router.put("", response_model=ProfileOut)
async def update_profile(body: ProfileIn, user_id: UserId, session: Session) -> Profile:
    profile = await get_or_create_profile(session, user_id)
    for field, value in body.model_dump().items():
        setattr(profile, field, value)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.get("/exclusions", response_model=list[ExcludedFoodOut])
async def list_exclusions(user_id: UserId, session: Session) -> list[ExcludedFood]:
    rows = await session.scalars(select(ExcludedFood).where(ExcludedFood.user_id == user_id))
    return list(rows)


@router.post("/exclusions", response_model=ExcludedFoodOut, status_code=status.HTTP_201_CREATED)
async def add_exclusion(body: ExcludedFoodIn, user_id: UserId, session: Session) -> ExcludedFood:
    await get_or_create_profile(session, user_id)
    row = ExcludedFood(user_id=user_id, **body.model_dump())
    session.add(row)
    await session.commit()
    return row


@router.delete("/exclusions/{exclusion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_exclusion(exclusion_id: uuid.UUID, user_id: UserId, session: Session) -> None:
    await session.execute(
        delete(ExcludedFood).where(ExcludedFood.id == exclusion_id, ExcludedFood.user_id == user_id)
    )
    await session.commit()
