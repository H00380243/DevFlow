"""SQLite database connection and session management."""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def get_db() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        SQLAlchemy Session instance.

    Raises:
        OperationalError: If SQLite file is not writable.
    """
    from app.core.config import get_settings
    settings = get_settings()

    # Extract database path from URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        # Create directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
