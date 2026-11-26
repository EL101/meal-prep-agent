from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

# Use in routes as `session: SessionDep`, then pass it to a service.
SessionDep = Annotated[AsyncSession, Depends(get_session)]
