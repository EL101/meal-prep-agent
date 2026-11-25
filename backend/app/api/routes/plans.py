import uuid
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import Queue, Session, UserId
from app.api.routes.profile import get_or_create_profile
from app.models import MealPlan
from app.schemas.api import JobAccepted, MealPlanOut, PlanEdit

router = APIRouter(prefix="/plans", tags=["plans"])


def next_monday(today: date | None = None) -> date:
    today = today or date.today()
    return today + timedelta(days=(7 - today.weekday()) % 7 or 7)


async def _owned_plan(session: Session, plan_id: uuid.UUID, user_id: uuid.UUID) -> MealPlan:
    plan = await session.get(MealPlan, plan_id)
    if plan is None or plan.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return plan


@router.post("", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_plan(user_id: UserId, session: Session, queue: Queue) -> JobAccepted:
    await get_or_create_profile(session, user_id)
    plan = MealPlan(user_id=user_id, week_start=next_monday())
    session.add(plan)
    await session.commit()
    await queue.enqueue_job("generate_plan", str(plan.id))
    return JobAccepted(id=plan.id, status="queued")


@router.get("", response_model=list[MealPlanOut])
async def list_plans(user_id: UserId, session: Session) -> list[MealPlan]:
    rows = await session.scalars(
        select(MealPlan).where(MealPlan.user_id == user_id).order_by(MealPlan.week_start.desc())
    )
    return list(rows)


@router.get("/{plan_id}", response_model=MealPlanOut)
async def read_plan(plan_id: uuid.UUID, user_id: UserId, session: Session) -> MealPlan:
    return await _owned_plan(session, plan_id, user_id)


@router.patch("/{plan_id}", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def edit_plan(
    plan_id: uuid.UUID, body: PlanEdit, user_id: UserId, session: Session, queue: Queue
) -> JobAccepted:
    """Lock/unlock/swap meals, then re-solve everything that isn't locked."""
    plan = await _owned_plan(session, plan_id, user_id)
    for meal in plan.meals:
        if meal.id in body.lock:
            meal.locked = True
        if meal.id in body.unlock or meal.id in body.swap:
            meal.locked = False
    plan.status = "queued"
    await session.commit()
    swap = [str(m) for m in body.swap]
    await queue.enqueue_job("generate_plan", str(plan.id), swap)
    return JobAccepted(id=plan.id, status="queued")
