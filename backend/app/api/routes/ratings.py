import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import Session, UserId
from app.models import Recipe, RecipeRating
from app.schemas.api import RatingIn

router = APIRouter(tags=["ratings"])


@router.post("/recipes/{recipe_id}/ratings", status_code=status.HTTP_201_CREATED)
async def rate_recipe(
    recipe_id: uuid.UUID, body: RatingIn, user_id: UserId, session: Session
) -> dict[str, str]:
    recipe = await session.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    rating = RecipeRating(user_id=user_id, recipe_id=recipe_id, **body.model_dump())
    session.add(rating)
    await session.commit()
    return {"id": str(rating.id)}
