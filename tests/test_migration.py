"""Tests for alembic initial migration — upgrade/downgrade (Feature 2).

Covers Test Inventory rows Y-AB of F002 data-model design doc:
- Y: INTG/db real SQLite + Base.metadata.create_all + relationship load
- Z: INTG/db alembic upgrade head creates 8 tables + indexes
- AA: INTG/db upgrade→downgrade→upgrade idempotent round-trip
- AB: INTG/db real SQLite FK enforcement on non-existent requirement_id

SEC: N/A — migration layer has no user input surface; DDL only.
"""

import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# SEC: N/A — migration layer has no user input surface (DDL only).


PROJECT_ROOT = "D:/github/DevFlow"
VENV_PYTHON = "D:/github/DevFlow/.venv/Scripts/python.exe"


@pytest.mark.real
def test_real_sqlite_create_all_and_relationship_load(tmp_path):
    """INTG/db Y (Feature 2): real SQLite file; create_all; insert + relationship load."""
    db_path = tmp_path / "feat2_y.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    from app.models import Base, Requirements, ReviewResults, init_db
    init_db(engine)
    # Insert parent + child, commit, then reload relationship on a fresh session
    with Session(bind=engine) as s:
        req = Requirements(
            id="REQ-20260705-001", original_text="原始需求", submitter_id="u1",
            current_stage="received", current_status="pending",
        )
        s.add(req)
        s.commit()
        s.add(ReviewResults(
            requirement_id=req.id, agent_role="business", business_value=4,
            technical_feasibility=4, roi=4, system_compatibility=4, verdict="通过",
        ))
        s.commit()
    # Reload on a fresh session to verify persistence + relationship load
    with Session(bind=engine) as s2:
        loaded = s2.get(Requirements, "REQ-20260705-001")
        assert loaded is not None
        assert len(loaded.review_results) == 1
        assert loaded.review_results[0].business_value == 4
    engine.dispose()
    # Data actually on disk
    assert db_path.exists() and db_path.stat().st_size > 0


@pytest.mark.real
def test_real_alembic_upgrade_creates_all_tables_and_indexes(tmp_path):
    """INTG/db Z (Feature 2): alembic upgrade head on real SQLite; 8 tables + indexes exist."""
    db_path = tmp_path / "feat2_z.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    env = {**os.environ, "DATABASE_URL": db_url, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    # Run alembic upgrade head via the project's alembic config
    result = subprocess.run(
        [VENV_PYTHON, "-m", "alembic", "-c", f"{PROJECT_ROOT}/alembic.ini", "upgrade", "head"],
        cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"alembic upgrade failed:\n{result.stderr}\n{result.stdout}"
    # Verify all 8 tables present + alembic_version stamped
    engine = create_engine(db_url)
    try:
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        expected_tables = {
            "requirements", "review_results", "design_results",
            "implementation_results", "delivery_archives", "status_history",
            "arbitration_requests", "idempotency_store",
        }
        assert expected_tables.issubset(tables), f"missing tables: {expected_tables - tables}"
        assert "alembic_version" in tables, "alembic_version table not stamped"
        # Verify indexes per design §3.2
        req_indexes = {ix["name"] for ix in insp.get_indexes("requirements")}
        assert any("submitter_id" in (ix["name"] or "") for ix in insp.get_indexes("requirements")) or \
               any(ix["column_names"] == ["submitter_id"] for ix in insp.get_indexes("requirements"))
        # composite index on (current_stage, current_status)
        req_idx_cols = [tuple(ix["column_names"]) for ix in insp.get_indexes("requirements")]
        assert ("current_stage", "current_status") in req_idx_cols
        # idempotency composite index
        idem_idx_cols = [tuple(ix["column_names"]) for ix in insp.get_indexes("idempotency_store")]
        assert ("sender_hash", "content_hash") in idem_idx_cols
    finally:
        engine.dispose()


@pytest.mark.real
def test_real_alembic_downgrade_then_upgrade_is_idempotent(tmp_path):
    """INTG/db AA (Feature 2): upgrade head → downgrade base → upgrade head; tables recreated."""
    db_path = tmp_path / "feat2_aa.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    env = {**os.environ, "DATABASE_URL": db_url, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    base_cmd = [VENV_PYTHON, "-m", "alembic", "-c", f"{PROJECT_ROOT}/alembic.ini"]
    # upgrade head
    r1 = subprocess.run(base_cmd + ["upgrade", "head"], cwd=PROJECT_ROOT, env=env,
                        capture_output=True, text=True, timeout=120)
    assert r1.returncode == 0, f"upgrade 1 failed:\n{r1.stderr}"
    # downgrade base (drops all tables)
    r2 = subprocess.run(base_cmd + ["downgrade", "base"], cwd=PROJECT_ROOT, env=env,
                        capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0, f"downgrade failed:\n{r2.stderr}"
    engine = create_engine(db_url)
    try:
        insp = inspect(engine)
        # After downgrade: business tables gone (only alembic_version may remain)
        biz = {"requirements", "review_results", "design_results",
               "implementation_results", "delivery_archives", "status_history",
               "arbitration_requests", "idempotency_store"}
        remaining = set(insp.get_table_names())
        assert not (biz & remaining), f"tables not dropped: {biz & remaining}"
    finally:
        engine.dispose()
    # upgrade head again — idempotent rebuild
    r3 = subprocess.run(base_cmd + ["upgrade", "head"], cwd=PROJECT_ROOT, env=env,
                        capture_output=True, text=True, timeout=120)
    assert r3.returncode == 0, f"upgrade 2 failed:\n{r3.stderr}"
    engine = create_engine(db_url)
    try:
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        assert "requirements" in tables
        assert "idempotency_store" in tables
        assert "review_results" in tables
    finally:
        engine.dispose()


@pytest.mark.real
def test_real_sqlite_fk_enforced_on_nonexistent_requirement(tmp_path):
    """INTG/db AB (Feature 2): real SQLite; ReviewResults with non-existent requirement_id raises."""
    db_path = tmp_path / "feat2_ab.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    # Enable FK enforcement at the engine level (per-connection pragma)
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    from app.models import Base, ReviewResults, init_db
    init_db(engine)
    with Session(bind=engine) as s:
        s.add(ReviewResults(
            requirement_id="REQ-NONEXISTENT", business_value=3,
            technical_feasibility=3, roi=3, system_compatibility=3, verdict="通过",
        ))
        with pytest.raises(IntegrityError):
            s.commit()
    engine.dispose()
