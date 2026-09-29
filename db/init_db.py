"""Database initialization — create tables and seed initial data."""

from __future__ import annotations

import logging

from db.base import Base
from db.session import engine

logger = logging.getLogger(__name__)


def init_db(seed: bool = True) -> None:
    """Create all tables and optionally seed demo data."""
    logger.info("Initializing database schema...")

    # Import all models so their tables are registered
    import models.assignment
    import models.employee
    import models.outcome
    import models.project
    import models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    if seed:
        from db.seed.seed_data import seed_database

        seed_database()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db(seed=True)
    print("Database initialized and seeded.")
