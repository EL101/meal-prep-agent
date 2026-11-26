from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserDep, SessionDep, SettingsDep
from app.schemas.user import UserRead
from app.services.user import AccountDeletionError, delete_user

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserRead)
async def read_me(user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: CurrentUserDep, session: SessionDep, settings: SettingsDep) -> None:
    try:
        await delete_user(session, user, settings)
    except AccountDeletionError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Couldn't delete the account. Try again."
        ) from None
