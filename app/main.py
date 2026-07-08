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

    @app.get("/api/dashboard/metrics")
    async def dashboard_metrics():
        """Return dashboard metrics (total requirements, review pass rate, in-progress count)."""
        from app.core.dashboard_service import DashboardService
        db = next(get_db())
        try:
            return DashboardService.get_metrics(db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

    @app.get("/api/requirements")
    async def list_requirements(
        page: int = 1,
        page_size: int = 10,
        stage: str | None = None,
        status: str | None = None,
        submitter: str | None = None,
        search: str | None = None,
    ):
        """Return paginated, filtered list of requirements."""
        from app.core.requirements_service import RequirementsService
        db = next(get_db())
        try:
            filters = {k: v for k, v in locals().items() if k != "db" and v is not None}
            return RequirementsService.get_requirements(db, filters)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

    @app.get("/api/requirements/{req_id}")
    async def get_requirement_detail(req_id: str):
        """Return full detail of a single requirement by ID."""
        from app.core.requirement_detail_service import RequirementDetailService
        db = next(get_db())
        try:
            return RequirementDetailService.get_detail(db, req_id)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

    return app
