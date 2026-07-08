"""Tests for auto_review_requirement — auto-trigger review after requirement creation."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, ReviewResults


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


@pytest.fixture
def requirement(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260707-001",
        original_text="用户反馈系统需要增加批量导入功能",
        summary="批量导入功能",
        submitter_id="user001",
        current_stage="review",
        current_status="PENDING_REVIEW",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


VALID_JSON = json.dumps({
    "business_value": 4,
    "technical_feasibility": 4,
    "roi": 4,
    "system_compatibility": 4,
    "verdict": "通过",
    "comments": "looks good",
})


@pytest.fixture(autouse=True)
def _stub_provider(monkeypatch):
    """Ensure CODE_AGENT_PROVIDER=stub so auto_review uses call_llm path."""
    monkeypatch.setenv("CODE_AGENT_PROVIDER", "stub")


class TestAutoReviewFunction:
    """Tests for auto_review_requirement() in isolation."""

    def test_auto_review_success_persists_scores(self, db_session, requirement):
        """Happy path: 3 agents score, scores persisted, status advanced."""
        from app.core.review_scoring import ReviewAgent, auto_review_requirement

        with patch.object(ReviewAgent, "call_llm", return_value=VALID_JSON):
            result = auto_review_requirement(db_session, "REQ-20260707-001")

        assert result is not None
        assert result.requirement_id == "REQ-20260707-001"
        assert len(result.scores) == 3

        rows = db_session.query(ReviewResults).filter(
            ReviewResults.requirement_id == "REQ-20260707-001"
        ).all()
        assert len(rows) == 3

        from app.core.state_machine import StateMachine, Status
        sm = StateMachine(db_session)
        new_status = sm.get_status("REQ-20260707-001")
        assert new_status == Status.IN_DESIGN

    def test_auto_review_with_reject_verdict(self, db_session, requirement):
        """When 2 agents reject, status becomes PENDING_ARBITRATION."""
        from app.core.review_scoring import ReviewAgent, auto_review_requirement

        reject_json = json.dumps({
            "business_value": 2,
            "technical_feasibility": 2,
            "roi": 2,
            "system_compatibility": 2,
            "verdict": "反对",
        })

        with patch.object(ReviewAgent, "call_llm", return_value=reject_json):
            result = auto_review_requirement(db_session, "REQ-20260707-001")

        assert result is not None
        assert result.final_decision.value == "NEEDS_ARBITRATION"

        from app.core.state_machine import StateMachine, Status
        sm = StateMachine(db_session)
        new_status = sm.get_status("REQ-20260707-001")
        assert new_status == Status.PENDING_ARBITRATION

    def test_auto_review_all_agents_fail(self, db_session, requirement):
        """When all agents raise NotImplementedError, auto_review raises."""
        from app.core.review_scoring import auto_review_requirement

        with pytest.raises(Exception) as excinfo:
            auto_review_requirement(db_session, "REQ-20260707-001")

        assert "REQ-20260707-001" in str(excinfo.value)

    def test_auto_review_nonexistent_req(self, db_session):
        """Non-existent requirement raises RequirementNotFoundError."""
        from app.core.review_scoring import auto_review_requirement

        with pytest.raises(Exception):
            auto_review_requirement(db_session, "REQ-NONEXIST-001")


class TestCreateReqKeepsWorking:
    """The route still returns the created requirement even if review fails."""

    def test_service_create_and_review_failure(self, db_session):
        """Creating a requirement via service + failed auto-review = requirement still exists."""
        from app.core.requirements_service import RequirementsService
        from app.core.review_scoring import auto_review_requirement

        result = RequirementsService.create_requirement(
            db_session,
            original_text="test",
            summary="test",
            submitter_id="user001",
        )
        req_id = result["id"]

        with pytest.raises(Exception):
            auto_review_requirement(db_session, req_id)

        row = db_session.query(Requirements).filter(Requirements.id == req_id).first()
        assert row is not None
        assert row.current_status == "PENDING_REVIEW"

