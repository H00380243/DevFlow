"""FastAPI application factory."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import get_db
from app.core.queue import init_huey
from app.core.webhook import WebhookHandler, WebhookValidationError, WebhookProcessingError


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

    # Initialize webhook handler
    webhook_handler = WebhookHandler()

    @app.post("/webhook/im/{platform}")
    async def webhook_im(platform: str, payload: dict):
        """Handle IM webhook requests.

        Args:
            platform: IM platform identifier.
            payload: Webhook payload from IM platform.

        Returns:
            Webhook response with status and message.
        """
        try:
            result = webhook_handler.handle_webhook(platform, payload)
            return result
        except WebhookValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except WebhookProcessingError as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app
