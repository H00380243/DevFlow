"""Tests for RequirementsService — F021 需求列表与筛选搜索."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
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


def seed_reqs(session, count: int, stage: str | None = None, status: str | None = None, submitter: str = "user001"):
    for i in range(count):
        req = Requirements(
            id=f"REQ-20260709-{i+1:04d}",
            original_text=f"需求{i+1}",
            summary=f"测试{i+1}",
            submitter_id=submitter if i < count // 2 else "user002",
            current_stage=stage or "implementation",
            current_status=status or "IN_IMPLEMENTATION",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(req)
    session.commit()


class TestRequirementsService:
    def test_basic_pagination(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 5)
        result = RequirementsService.get_requirements(db_session, {})
        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 10

    def test_page_size_10(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 15)
        result = RequirementsService.get_requirements(db_session, {"page_size": 10})
        assert result["total"] == 15
        assert len(result["items"]) == 10

    def test_second_page(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 15)
        result = RequirementsService.get_requirements(db_session, {"page": 2, "page_size": 10})
        assert result["total"] == 15
        assert len(result["items"]) == 5

    def test_page_out_of_range(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 10)
        result = RequirementsService.get_requirements(db_session, {"page": 2, "page_size": 10})
        assert result["total"] == 10
        assert len(result["items"]) == 0

    def test_stage_filter(self, db_session):
        from app.core.requirements_service import RequirementsService

        for i, stage in enumerate(["review", "design", "implementation"]):
            req = Requirements(
                id=f"REQ-20260709-{i+1:04d}",
                original_text=f"需求{i+1}",
                summary=f"测试{i+1}",
                submitter_id="user001",
                current_stage=stage,
                current_status="PENDING_REVIEW",
                created_at=datetime.now(timezone.utc),
            )
            db_session.add(req)
        db_session.commit()
        result = RequirementsService.get_requirements(db_session, {"stage": "design"})
        assert result["total"] == 1
        assert result["items"][0]["current_stage"] == "design"

    def test_search_by_id(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 3)
        result = RequirementsService.get_requirements(db_session, {"search": "REQ-20260709-0001"})
        assert result["total"] == 1
        assert result["items"][0]["id"] == "REQ-20260709-0001"

    def test_search_by_summary(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 5)
        result = RequirementsService.get_requirements(db_session, {"search": "测试2"})
        assert result["total"] >= 1

    def test_empty_search_returns_all(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 3)
        result = RequirementsService.get_requirements(db_session, {"search": ""})
        assert result["total"] == 3

    def test_combined_filters(self, db_session):
        from app.core.requirements_service import RequirementsService

        req1 = Requirements(id="REQ-20260709-0001", original_text="a", summary="a", submitter_id="user001", current_stage="review", current_status="PENDING_REVIEW")
        req2 = Requirements(id="REQ-20260709-0002", original_text="b", summary="b", submitter_id="user002", current_stage="design", current_status="IN_DESIGN")
        db_session.add_all([req1, req2])
        db_session.commit()
        result = RequirementsService.get_requirements(db_session, {"stage": "design", "submitter": "user002"})
        assert result["total"] == 1
        assert result["items"][0]["id"] == "REQ-20260709-0002"

    def test_page_zero_raises(self, db_session):
        from app.core.requirements_service import RequirementsService

        with pytest.raises(ValueError, match="page must be >= 1"):
            RequirementsService.get_requirements(db_session, {"page": 0})

    def test_invalid_page_size_raises(self, db_session):
        from app.core.requirements_service import RequirementsService

        with pytest.raises(ValueError, match="page_size must be 10, 20, or 50"):
            RequirementsService.get_requirements(db_session, {"page_size": 5})

    def test_empty_db(self, db_session):
        from app.core.requirements_service import RequirementsService

        result = RequirementsService.get_requirements(db_session, {})
        assert result["total"] == 0
        assert result["items"] == []

    def test_exact_page_size_boundary(self, db_session):
        from app.core.requirements_service import RequirementsService

        seed_reqs(db_session, 50)
        result = RequirementsService.get_requirements(db_session, {"page_size": 50})
        assert result["total"] == 50
        assert len(result["items"]) == 50
