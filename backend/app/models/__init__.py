"""SQLAlchemy ORM models (database tables), one module per table.

Import each model here so Alembic autogenerate can find it through Base.metadata.
"""

from app.db import Base
from app.models.user import User

__all__ = ["Base", "User"]
