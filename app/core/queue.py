"""Huey task queue configuration."""

import os
from pathlib import Path

from huey import Huey
from huey.storage import SqliteStorage


def init_huey() -> Huey:
    """Initialize Huey task queue with SQLite backend.

    Returns:
        Configured Huey instance.

    Raises:
        HueyException: If Huey initialization fails.
    """
    from app.core.config import get_settings
    settings = get_settings()

    huey_url = settings.HUEY_URL
    if not huey_url:
        huey_url = "sqlite:///data/huey_queue.db"

    # Extract path from URL for directory creation
    if huey_url.startswith("sqlite:///"):
        db_path = huey_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    else:
        db_path = huey_url

    return Huey(
        name="demandflow",
        storage_class=SqliteStorage,
        filename=db_path,
        immediate=False,
    )
