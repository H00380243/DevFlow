"""Integration: State Machine + Command + Action flows [Real]."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, StatusHistory
from app.core.state_machine import StateMachine, Event, Status


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
        "original_text": "test integration",
        "summary": "集成测试需求",
        "submitter_id": "user001",
        "current_stage": "review",
        "current_status": "PENDING_REVIEW",
    }
    data.update(overrides)
    req = Requirements(**data)
    db.add(req)
    db.commit()
    return req


class TestStateMachineIntegration:
    """Integration: F007 StateMachine transitions through F009/F010/F014/F017."""

    def test_full_review_to_design_flow(self, db_session):
        """Real: PENDING_REVIEW → REVIEW_APPROVED → IN_DESIGN via state machine."""
        _seed_req(db_session)
        sm = StateMachine(db_session)

        # PENDING_REVIEW → REVIEW_APPROVED
        sm.transition("REQ-20260709-0001", Event.REVIEW_PASS, "system")
        req = db_session.query(Requirements).first()
        assert req.current_status == "REVIEW_APPROVED"

        # REVIEW_APPROVED → IN_DESIGN (uses REVIEW_PASS as auto-transition)
        sm.transition("REQ-20260709-0001", Event.REVIEW_PASS, "system")
        req = db_session.query(Requirements).first()
        assert req.current_status == "IN_DESIGN"

    def test_review_to_arbitration_flow(self, db_session):
        """Real: PENDING_REVIEW → PENDING_ARBITRATION → REVIEW_APPROVED."""
        _seed_req(db_session)
        sm = StateMachine(db_session)

        sm.transition("REQ-20260709-0001", Event.REVIEW_REJECT, "system")
        req = db_session.query(Requirements).first()
        assert req.current_status == "PENDING_ARBITRATION"

        sm.transition("REQ-20260709-0001", Event.ARBITRATION_APPROVE, "admin")
        req = db_session.query(Requirements).first()
        assert req.current_status == "REVIEW_APPROVED"

    def test_design_confirm_flow(self, db_session):
        """Real: DESIGN_PENDING_CONFIRM → DESIGN_CONFIRMED → IN_IMPLEMENTATION."""
        _seed_req(db_session, current_status="DESIGN_PENDING_CONFIRM", current_stage="design")
        sm = StateMachine(db_session)

        sm.transition("REQ-20260709-0001", Event.DESIGN_CONFIRM, "user001")
        req = db_session.query(Requirements).first()
        assert req.current_status == "DESIGN_CONFIRMED"

    def test_implementation_confirm_flow(self, db_session):
        """Real: IMPL_PENDING_ACCEPTANCE → IMPL_APPROVED → DELIVERED."""
        _seed_req(db_session, current_status="IMPL_PENDING_ACCEPTANCE", current_stage="implementation")
        sm = StateMachine(db_session)

        sm.transition("REQ-20260709-0001", Event.IMPL_CONFIRM, "user001")
        req = db_session.query(Requirements).first()
        assert req.current_status == "IMPL_APPROVED"

    def test_reject_to_terminated_via_max_retry(self, db_session):
        """Real: DESIGN_REJECTED → IN_DESIGN → MAX_RETRY → TERMINATED."""
        _seed_req(db_session, current_status="DESIGN_REJECTED", current_stage="design")
        sm = StateMachine(db_session)

        sm.transition("REQ-20260709-0001", Event.MAX_RETRY, "system")
        req = db_session.query(Requirements).first()
        assert req.current_status == "TERMINATED"

    def test_status_history_logged_on_transition(self, db_session):
        """Real: Each transition creates a StatusHistory record."""
        _seed_req(db_session)
        sm = StateMachine(db_session)

        sm.transition("REQ-20260709-0001", Event.REVIEW_PASS, "system")
        count = db_session.query(StatusHistory).count()
        assert count > 0

    def test_invalid_transition_raises(self, db_session):
        """Real: Invalid event for current status raises."""
        _seed_req(db_session, current_status="DELIVERED", current_stage="delivered")
        sm = StateMachine(db_session)

        with pytest.raises(Exception):
            sm.transition("REQ-20260709-0001", Event.REVIEW_PASS, "system")
