"""SQLAlchemy ORM models (database tables), one module per table.

Import each model here so Alembic autogenerate can find it through Base.metadata, e.g.:

    from app.models.user import User
"""

from app.db import Base

__all__ = ["Base"]
