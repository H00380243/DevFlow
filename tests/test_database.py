"""Tests for app.core.database — SQLite connection and session management."""

import pytest

from sqlalchemy import text
from sqlalchemy.orm import Session

# SEC: N/A — database session utility with no user-facing input; no injection
# surface (DATABASE_URL is operator-controlled config, not request input).


# [unit]
class TestGetDb:
    """Test get_db generator."""

    def test_get_db_returns_session_and_closes(self, tmp_path, monkeypatch):
        """FUNC/happy — C: Returns open Session, closes it after use."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        from app.core.database import get_db
        gen = get_db()
        session = next(gen)
        assert isinstance(session, Session)
        assert session.is_active  # usable while in scope

        # Spy on close() to verify it is invoked when the generator exhausts.
        # (is_active does not reflect closed state in SQLAlchemy 2.0; a call
        # spy is the reliable, mutation-relevant way to verify the finally.)
        close_calls = []
        original_close = session.close

        def tracking_close():
            close_calls.append(1)
            original_close()

        session.close = tracking_close
        try:
            next(gen)  # resume past yield → finally runs session.close()
        except StopIteration:
            pass
        assert len(close_calls) == 1  # finally closed the session exactly once

    def test_get_db_raises_on_unwritable_path(self, tmp_path, monkeypatch):
        """FUNC/error — F: DATABASE_URL whose parent is a regular file raises OSError.

        A regular file blocking the parent directory path makes SQLite unable to
        create the db file; get_db must surface this as an error rather than
        silently returning a session that cannot work.
        """
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory")
        db_path = blocker / "test.db"  # parent 'blocker' is a file, not a dir
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        from app.core.database import get_db
        gen = get_db()
        with pytest.raises(OSError):
            next(gen)

    def test_get_db_creates_directory_if_missing(self, tmp_path, monkeypatch):
        """BNDRY/edge — G: Auto-create directory if DATABASE_URL path missing."""
        db_dir = tmp_path / "nonexistent" / "deep" / "path"
        db_path = db_dir / "test.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        from app.core.database import get_db
        gen = get_db()
        session = next(gen)
        assert isinstance(session, Session)
        assert db_dir.exists()  # directory auto-created
        try:
            next(gen)
        except StopIteration:
            pass


# [integration]
class TestGetDbIntegration:
    """Integration tests for database connection — real SQLite file."""

    @pytest.mark.real
    def test_get_db_session_executes_query(self, tmp_path, monkeypatch):
        """INTG/db — J (Feature 1): Real SQLite session can execute a query and return data."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        from app.core.database import get_db
        gen = get_db()
        session = next(gen)
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        try:
            next(gen)
        except StopIteration:
            pass
