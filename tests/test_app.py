"""Tests for app.main — FastAPI application factory."""

import pytest

from fastapi import FastAPI

# SEC: N/A — application factory with no user-facing input at construction time;
# request-handling security is covered by downstream features (F003 IM Webhook).


# [unit]
class TestCreateApp:
    """Test create_app factory function."""

    def test_create_app_returns_fastapi_instance(self, monkeypatch):
        """FUNC/happy — A: Returns FastAPI instance with correct title and version."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///data/test.db")
        monkeypatch.setenv("HUEY_URL", "sqlite:///data/test_huey.db")

        from app.main import create_app
        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "DemandFlow"
        assert app.version == "0.1.0"
        assert app.state.huey is not None  # Huey instance attached

    def test_create_app_uses_default_config_when_not_set(self, monkeypatch):
        """FUNC/error — E: Missing config uses defaults, does not raise."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("HUEY_URL", raising=False)

        from app.main import create_app
        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "DemandFlow"
