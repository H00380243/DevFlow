"""Tests for app.core.queue — Huey task queue configuration."""

import pytest

from huey import Huey

# SEC: N/A — queue configuration utility with no user-facing input; HUEY_URL is
# operator-controlled config, not request input.


# [unit]
class TestInitHuey:
    """Test init_huey function."""

    def test_init_huey_returns_instance(self, tmp_path, monkeypatch):
        """FUNC/happy — D: Returns a Huey instance backed by SQLite storage."""
        huey_path = tmp_path / "test_huey.db"
        monkeypatch.setenv("HUEY_URL", str(huey_path))

        from app.core.queue import init_huey
        huey = init_huey()
        assert isinstance(huey, Huey)
        assert huey.name == "demandflow"

    def test_init_huey_uses_default_on_empty_string(self, monkeypatch):
        """BNDRY/edge — H: Empty HUEY_URL falls back to default SQLite path."""
        monkeypatch.setenv("HUEY_URL", "")

        from app.core.queue import init_huey
        huey = init_huey()
        assert isinstance(huey, Huey)
        # Verify the default path is actually used (not just that a Huey is returned)
        assert huey.storage.filename.endswith("huey_queue.db")


# [integration]
class TestInitHueyIntegration:
    """Integration tests for Huey queue — real SQLite-backed Huey instance."""

    @pytest.mark.real
    def test_init_huey_can_enqueue_task(self, tmp_path, monkeypatch):
        """INTG/db — K (Feature 1): Huey instance can enqueue a task (storage write works)."""
        huey_path = tmp_path / "test_huey.db"
        monkeypatch.setenv("HUEY_URL", str(huey_path))

        from app.core.queue import init_huey
        huey = init_huey()

        @huey.task()
        def dummy_task():
            return "done"

        result = dummy_task()
        assert result is not None
        pending = huey.pending()
        assert len(pending) >= 1  # task actually reached the SQLite-backed queue
