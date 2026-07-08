"""Tests for RequirementActionService — F023 看板操作与 IM 同步."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, StatusHistory
from app.core.requirement_action_service import (
    RequirementActionService,
    ActionValidationError,
)
from app.core.state_machine import StateMachine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _seed_req(db, **overrides):
    data = {
        "id": "REQ-20260709-0001",
        "original_text": "test",
        "summary": "测试需求",
        "submitter_id": "user001",
        "current_stage": "review",
        "current_status": "PENDING_REVIEW",
    }
    data.update(overrides)
    req = Requirements(**data)
    db.add(req)
    db.commit()
    return req


class TestActionValidation:
    def test_empty_req_id_raises(self, db_session):
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        with pytest.raises(ActionValidationError, match="req_id"):
            svc.execute_action("", "confirm", "user001")

    def test_invalid_action_raises(self, db_session):
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        with pytest.raises(ActionValidationError, match="action must be"):
            svc.execute_action("REQ-001", "invalid", "user001")

    def test_empty_user_id_raises(self, db_session):
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        with pytest.raises(ActionValidationError, match="user_id"):
            svc.execute_action("REQ-001", "confirm", "")

    def test_reject_without_reason_raises(self, db_session):
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        with pytest.raises(ActionValidationError, match="reason"):
            svc.execute_action("REQ-001", "reject", "user001", "")


class TestExecuteAction:
    def test_confirm_pending_review_transitions(self, db_session):
        _seed_req(db_session)
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        result = svc.execute_action("REQ-20260709-0001", "confirm", "user001")
        assert result["status"] == "ok"
        req = db_session.query(Requirements).first()
        assert req.current_status == "REVIEW_APPROVED"

    def test_reject_pending_review_transitions(self, db_session):
        _seed_req(db_session)
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        result = svc.execute_action("REQ-20260709-0001", "reject", "user001", "质量不足")
        assert result["status"] == "ok"
        req = db_session.query(Requirements).first()
        assert req.current_status == "PENDING_ARBITRATION"

    def test_history_logged(self, db_session):
        _seed_req(db_session)
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        svc.execute_action("REQ-20260709-0001", "confirm", "user001")
        count = db_session.query(StatusHistory).count()
        assert count > 0

    def test_nonexistent_req_returns_error(self, db_session):
        sm = StateMachine(db_session)
        svc = RequirementActionService(db_session, sm)
        result = svc.execute_action("REQ-NOPE", "confirm", "user001")
        assert result["status"] == "error"
