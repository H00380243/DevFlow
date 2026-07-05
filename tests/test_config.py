"""Tests for app.core.config — Settings configuration loading."""

import pytest

# SEC: N/A — configuration loader with no user-facing input; environment
# variables are operator-controlled, not request input.


# [unit]
class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_loads_env_vars(self, monkeypatch):
        """FUNC/happy — B: Settings instance fields populated."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///data/test.db")
        monkeypatch.setenv("HUEY_URL", "sqlite:///data/test_huey.db")

        from app.core.config import get_settings
        settings = get_settings()

        assert settings.DATABASE_URL == "sqlite:///data/test.db"
        assert settings.HUEY_URL == "sqlite:///data/test_huey.db"

    def test_get_settings_works_without_dotenv(self, monkeypatch):
        """BNDRY/edge — I: .env file missing, use system env vars."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("HUEY_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "sqlite:///fallback.db")
        monkeypatch.setenv("HUEY_URL", "sqlite:///fallback_huey.db")

        from app.core.config import get_settings
        settings = get_settings()

        assert settings.DATABASE_URL == "sqlite:///fallback.db"

    def test_get_settings_uses_defaults_when_not_set(self, monkeypatch):
        """FUNC/error — E: Missing config uses defaults, does not raise."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("HUEY_URL", raising=False)

        from app.core.config import get_settings
        settings = get_settings()

        assert settings.DATABASE_URL == "sqlite:///data/demandflow.db"
        assert settings.HUEY_URL == "sqlite:///data/huey_queue.db"
