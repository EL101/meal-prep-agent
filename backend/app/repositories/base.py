from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base


class BaseRepository[ModelT: Base]:
    """Generic CRUD helpers. Subclass per model, e.g. `class UserRepository(BaseRepository[User])`
    with `model = User`, and add model-specific queries there."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: Any) -> ModelT | None:
        return await self.session.get(self.model, id)

    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
