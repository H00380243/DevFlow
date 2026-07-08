"""Tests for RequirementDetailService — F022 需求详情页."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, StatusHistory
from app.core.requirement_detail_service import RequirementDetailService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _seed_requirement(db, **overrides):
    data = {
        "id": "REQ-20260709-0001",
        "original_text": "test requirement",
        "summary": "测试需求详情",
        "submitter_id": "user001",
        "submitter_name": "用户1",
        "current_stage": "review",
        "current_status": "PENDING_REVIEW",
    }
    data.update(overrides)
    req = Requirements(**data)
    db.add(req)
    db.commit()
    return req


class TestGetDetail:
    def test_returns_full_info(self, db_session):
        req = _seed_requirement(db_session)
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert result["id"] == "REQ-20260709-0001"
        assert result["summary"] == "测试需求详情"
        assert result["current_stage"] == "review"

    def test_includes_timeline_empty(self, db_session):
        req = _seed_requirement(db_session)
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert result["timeline"] == []

    def test_includes_timeline_with_history(self, db_session):
        req = _seed_requirement(db_session)
        db_session.add(StatusHistory(
            requirement_id=req.id, from_status=None, to_status="PENDING_REVIEW",
            trigger_event="SUBMIT", trigger_user="user001",
        ))
        db_session.commit()
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert len(result["timeline"]) == 1
        assert result["timeline"][0]["to_status"] == "PENDING_REVIEW"

    def test_returns_counts(self, db_session):
        req = _seed_requirement(db_session)
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert result["review_count"] == 0
        assert result["design_count"] == 0
        assert result["implementation_count"] == 0

    def test_empty_req_id_raises(self, db_session):
        with pytest.raises(ValueError, match="req_id is required"):
            RequirementDetailService.get_detail(db_session, "")

    def test_nonexistent_id_raises(self, db_session):
        with pytest.raises(LookupError, match="not found"):
            RequirementDetailService.get_detail(db_session, "REQ-NONEXIST")

    def test_returns_tags_as_list(self, db_session):
        req = _seed_requirement(db_session, tags=["urgent", "frontend"])
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert result["tags"] == ["urgent", "frontend"]

    def test_returns_none_tags_as_empty(self, db_session):
        req = _seed_requirement(db_session, tags=None)
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert result["tags"] == []

    def test_created_at_isoformat(self, db_session):
        from datetime import datetime
        now = datetime(2026, 7, 9, 12, 0, 0)
        req = _seed_requirement(db_session, created_at=now)
        result = RequirementDetailService.get_detail(db_session, req.id)
        assert result["created_at"] == "2026-07-09T12:00:00"

    def test_timeline_sorted_by_triggered_at(self, db_session):
        from datetime import datetime
        req = _seed_requirement(db_session)
        db_session.add(StatusHistory(
            requirement_id=req.id, to_status="IN_DESIGN",
            triggered_at=datetime(2026, 7, 9, 10, 0, 0),
        ))
        db_session.add(StatusHistory(
            requirement_id=req.id, to_status="PENDING_REVIEW",
            triggered_at=datetime(2026, 7, 9, 9, 0, 0),
        ))
        db_session.commit()
        result = RequirementDetailService.get_detail(db_session, req.id)
        statuses = [t["to_status"] for t in result["timeline"]]
        assert statuses == ["PENDING_REVIEW", "IN_DESIGN"]
