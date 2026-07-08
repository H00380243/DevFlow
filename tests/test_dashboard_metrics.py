"""Tests for DashboardService — F020 看板首页指标."""

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements


@pytest.fixture
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


def seed_requirements(session, statuses: list[str]):
    for i, status in enumerate(statuses):
        req = Requirements(
            id=f"REQ-20260709-{i+1:03d}",
            original_text=f"需求{i+1}",
            summary=f"测试{i+1}",
            submitter_id="user001",
            current_stage="implementation",
            current_status=status,
        )
        session.add(req)
    session.commit()


class TestDashboardMetrics:
    def test_happy_path_mixed(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, [
            "REVIEW_APPROVED", "REVIEW_APPROVED", "REVIEW_APPROVED",
            "REVIEW_APPROVED", "REVIEW_APPROVED",
            "PENDING_REVIEW", "PENDING_REVIEW", "PENDING_REVIEW",
            "REJECTED", "TERMINATED",
        ])
        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 10
        assert result["review_pass_rate"] == 50.0
        assert result["in_progress_count"] == 8

    def test_single_approved(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, ["REVIEW_APPROVED"])
        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 1
        assert result["review_pass_rate"] == 100.0
        assert result["in_progress_count"] == 1

    def test_empty_db(self, db_session):
        from app.core.dashboard_service import DashboardService

        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 0
        assert result["review_pass_rate"] is None
        assert result["in_progress_count"] == 0

    def test_single_rejected(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, ["REJECTED"])
        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 1
        assert result["review_pass_rate"] == 0.0
        assert result["in_progress_count"] == 0

    def test_all_approved_1000(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, ["REVIEW_APPROVED"] * 1000)
        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 1000
        assert result["review_pass_rate"] == 100.0
        assert result["in_progress_count"] == 1000

    def test_connection_error_500(self):
        from app.core.dashboard_service import DashboardService

        bad_engine = create_engine("sqlite:///nonexistent/path/test.db", echo=False)
        BadSession = sessionmaker(bind=bad_engine)
        session = BadSession()
        with pytest.raises(Exception):
            DashboardService.get_metrics(session)
        session.close()

    def test_empty_table_no_error(self, db_engine):
        from app.core.dashboard_service import DashboardService

        SessionLocal = sessionmaker(bind=db_engine)
        session = SessionLocal()
        result = DashboardService.get_metrics(session)
        assert result["total_requirements"] == 0
        session.close()

    def test_integration_real_db(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, [
            "REVIEW_APPROVED", "IN_DESIGN", "DELIVERED", "PENDING_REVIEW", "TERMINATED",
        ])
        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 5
        assert result["review_pass_rate"] == pytest.approx(60.0, abs=0.1)
        assert result["in_progress_count"] == 3

    def test_rate_exact_100(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, ["IN_IMPLEMENTATION"])
        result = DashboardService.get_metrics(db_session)
        assert result["total_requirements"] == 1
        assert result["review_pass_rate"] == 100.0

    def test_partial_query_failure(self, db_session):
        from app.core.dashboard_service import DashboardService

        seed_requirements(db_session, ["REVIEW_APPROVED"])
        import app.core.dashboard_service as svc
        original_approved = svc.APPROVED_STATES
        svc.APPROVED_STATES = None
        try:
            result = DashboardService.get_metrics(db_session)
            assert "errors" in result
        finally:
            svc.APPROVED_STATES = original_approved
