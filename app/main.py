"""FastAPI application factory."""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import get_db
from app.core.queue import init_huey


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI instance.

    Raises:
        ConfigError: If required configuration is missing.
    """
    settings = get_settings()

    # Initialize database
    from app.core.database import get_db

    # Initialize Huey queue
    huey = init_huey()

    # Create FastAPI instance
    app = FastAPI(title="DemandFlow", version="0.1.0")

    # Store huey instance on app for later use
    app.state.huey = huey

    return app
