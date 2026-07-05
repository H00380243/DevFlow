"""Tests for StateMachine — F007 状态机引擎."""

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Requirements, StatusHistory
from app.core.state_machine import (
    Event,
    InvalidTransitionError,
    RequirementNotFoundError,
    StateMachine,
    Status,
)


@pytest.fixture
def db_engine(tmp_path):
    """Create a file-based SQLite engine for testing."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a session for testing."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def state_machine(db_session):
    """Create a StateMachine instance with a test session."""
    return StateMachine(db_session)


def _create_requirement(
    session: Session,
    req_id: str = "REQ-20260705-001",
    status: str = "PENDING_REVIEW",
    stage: str = "review",
) -> Requirements:
    """Create a test requirement in the database."""
    req = Requirements(
        id=req_id,
        original_text="Test requirement",
        submitter_id="user1",
        current_stage=stage,
        current_status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(req)
    session.commit()
    return req


class TestTransitionReviewApprovedToInDesign:
    """Test A: FUNC/happy — auto-transition REVIEW_APPROVED → IN_DESIGN."""

    def test_auto_transition_to_in_design(self, db_session, state_machine):
        _create_requirement(db_session, status="REVIEW_APPROVED", stage="review")
        result = state_machine.transition("REQ-20260705-001", Event.REVIEW_PASS)
        assert result == Status.IN_DESIGN


class TestTransitionDesignConfirmedToInImplementation:
    """Test B: FUNC/happy — auto-transition DESIGN_CONFIRMED → IN_IMPLEMENTATION."""

    def test_auto_transition_to_in_implementation(self, db_session, state_machine):
        _create_requirement(db_session, status="DESIGN_CONFIRMED", stage="design")
        result = state_machine.transition("REQ-20260705-001", Event.DESIGN_CONFIRM)
        assert result == Status.IN_IMPLEMENTATION


class TestTransitionImplApprovedToDelivered:
    """Test C: FUNC/happy — auto-transition IMPL_APPROVED → DELIVERED."""

    def test_auto_transition_to_delivered(self, db_session, state_machine):
        _create_requirement(db_session, status="IMPL_APPROVED", stage="implementation")
        result = state_machine.transition("REQ-20260705-001", Event.IMPL_CONFIRM)
        assert result == Status.DELIVERED


class TestConcurrentTransitions:
    """Test D: FUNC/happy — 2 concurrent reqs transition independently."""

    def test_concurrent_transitions_independent(self, db_session):
        _create_requirement(db_session, "REQ-20260705-001", "PENDING_REVIEW", "review")
        _create_requirement(db_session, "REQ-20260705-002", "PENDING_REVIEW", "review")

        sm1 = StateMachine(db_session)
        sm2 = StateMachine(db_session)

        result1 = sm1.transition("REQ-20260705-001", Event.REVIEW_PASS)
        result2 = sm2.transition("REQ-20260705-002", Event.REVIEW_PASS)

        assert result1 == Status.REVIEW_APPROVED
        assert result2 == Status.REVIEW_APPROVED


class TestPersistenceRecovery:
    """Test E: FUNC/happy — transition → crash → load_state returns persisted status."""

    def test_persistence_recovery(self, db_engine, db_session):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        sm = StateMachine(db_session)
        sm.transition("REQ-20260705-001", Event.REVIEW_PASS)

        SessionLocal = sessionmaker(bind=db_engine)
        new_session = SessionLocal()
        sm_new = StateMachine(new_session)
        status = sm_new.get_status("REQ-20260705-001")
        assert status == Status.REVIEW_APPROVED
        new_session.close()


class TestTransitionReturnsCorrectStatus:
    """Test F: FUNC/happy — transition returns correct Status + StatusHistory row."""

    def test_transition_returns_status_and_history(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        result = state_machine.transition("REQ-20260705-001", Event.REVIEW_PASS, "user1")
        assert result == Status.REVIEW_APPROVED

        history = db_session.query(StatusHistory).filter_by(
            requirement_id="REQ-20260705-001"
        ).first()
        assert history is not None
        assert history.from_status == "PENDING_REVIEW"
        assert history.to_status == "REVIEW_APPROVED"
        assert history.trigger_event == "REVIEW_PASS"
        assert history.trigger_user == "user1"


class TestInvalidTransitionDelivered:
    """Test G: FUNC/error — DELIVERED + REVIEW_PASS → InvalidTransitionError."""

    def test_invalid_transition_delivered(self, db_session, state_machine):
        _create_requirement(db_session, status="DELIVERED", stage="delivery")
        with pytest.raises(InvalidTransitionError):
            state_machine.transition("REQ-20260705-001", Event.REVIEW_PASS)


class TestInvalidTransitionRejected:
    """Test H: FUNC/error — REJECTED + DESIGN_CONFIRM → InvalidTransitionError."""

    def test_invalid_transition_rejected(self, db_session, state_machine):
        _create_requirement(db_session, status="REJECTED", stage="review")
        with pytest.raises(InvalidTransitionError):
            state_machine.transition("REQ-20260705-001", Event.DESIGN_CONFIRM)


class TestRequirementNotFound:
    """Test I: FUNC/error — nonexistent req → RequirementNotFoundError."""

    def test_requirement_not_found(self, state_machine):
        with pytest.raises(RequirementNotFoundError):
            state_machine.transition("NONEXISTENT-001", Event.SUBMIT)


class TestTimeoutLoop:
    """Test J: BNDRY/edge — TIMEOUT 3rd time at PENDING_ARBITRATION → stays."""

    def test_timeout_loop_third_time(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_ARBITRATION", stage="arbitration")
        for _ in range(3):
            state_machine.transition("REQ-20260705-001", Event.TIMEOUT)
        status = state_machine.get_status("REQ-20260705-001")
        assert status == Status.PENDING_ARBITRATION


class TestDesignRetryMaxExceeded:
    """Test K: BNDRY/edge — DESIGN_RETRY 4th time → TERMINATED."""

    def test_design_retry_max_exceeded(self, db_session, state_machine):
        _create_requirement(db_session, status="DESIGN_REJECTED", stage="design")
        for _ in range(3):
            # DESIGN_REJECTED → IN_DESIGN (retry)
            state_machine.transition("REQ-20260705-001", Event.DESIGN_RETRY)
            # IN_DESIGN → DESIGN_PENDING_CONFIRM (complete design)
            state_machine.transition("REQ-20260705-001", Event.DESIGN_COMPLETE)
            # DESIGN_PENDING_CONFIRM → DESIGN_REJECTED (reject again)
            state_machine.transition("REQ-20260705-001", Event.DESIGN_REJECT)
        # 4th retry should terminate
        result = state_machine.transition("REQ-20260705-001", Event.DESIGN_RETRY)
        assert result == Status.TERMINATED


class TestImplRetryMaxExceeded:
    """Test L: BNDRY/edge — IMPL_RETRY 4th time → TERMINATED."""

    def test_impl_retry_max_exceeded(self, db_session, state_machine):
        _create_requirement(db_session, status="IMPL_REJECTED", stage="implementation")
        for _ in range(3):
            # IMPL_REJECTED → IN_IMPLEMENTATION (retry)
            state_machine.transition("REQ-20260705-001", Event.IMPL_RETRY)
            # IN_IMPLEMENTATION → IMPL_PENDING_ACCEPTANCE (complete)
            state_machine.transition("REQ-20260705-001", Event.IMPL_COMPLETE)
            # IMPL_PENDING_ACCEPTANCE → IMPL_REJECTED (reject again)
            state_machine.transition("REQ-20260705-001", Event.IMPL_REJECT)
        # 4th retry should terminate
        result = state_machine.transition("REQ-20260705-001", Event.IMPL_RETRY)
        assert result == Status.TERMINATED


class TestPendingReviewRejectToArbitration:
    """Test M: FUNC/state — PENDING_REVIEW + REVIEW_REJECT → PENDING_ARBITRATION."""

    def test_review_reject_to_arbitration(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        result = state_machine.transition("REQ-20260705-001", Event.REVIEW_REJECT)
        assert result == Status.PENDING_ARBITRATION


class TestDesignRejectedRetryToInDesign:
    """Test N: FUNC/state — DESIGN_REJECTED + DESIGN_RETRY → IN_DESIGN."""

    def test_design_retry_to_in_design(self, db_session, state_machine):
        _create_requirement(db_session, status="DESIGN_REJECTED", stage="design")
        result = state_machine.transition("REQ-20260705-001", Event.DESIGN_RETRY)
        assert result == Status.IN_DESIGN


class TestNoneReqId:
    """Test O: BNDRY/edge — None req_id → RequirementNotFoundError."""

    def test_none_req_id(self, state_machine):
        with pytest.raises(RequirementNotFoundError):
            state_machine.transition(None, Event.SUBMIT)


class TestDbPersistence:
    """Test P: INTG/db — transition + SELECT from SQLite."""

    def test_db_persistence(self, db_engine, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        state_machine.transition("REQ-20260705-001", Event.REVIEW_PASS)

        result = db_session.execute(
            text("SELECT current_status FROM requirements WHERE id = :req_id"),
            {"req_id": "REQ-20260705-001"},
        )
        row = result.first()
        assert row.current_status == "REVIEW_APPROVED"

        history = db_session.execute(
            text("SELECT COUNT(*) FROM status_history WHERE requirement_id = :req_id"),
            {"req_id": "REQ-20260705-001"},
        )
        count = history.scalar()
        assert count == 1


class TestLoadStateReadsSavedState:
    """Test Q: INTG/db — save_state + new session load_state."""

    def test_load_state_reads_saved_state(self, db_engine, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        state_machine.transition("REQ-20260705-001", Event.REVIEW_PASS)

        SessionLocal = sessionmaker(bind=db_engine)
        new_session = SessionLocal()
        sm_new = StateMachine(new_session)
        loaded_status = sm_new.load_state("REQ-20260705-001")
        assert loaded_status == Status.REVIEW_APPROVED
        new_session.close()


class TestConcurrentTransitionsPerformance:
    """Test R: PERF/concurrent — 5 concurrent transitions on 5 different reqs."""

    def test_concurrent_transitions_no_corruption(self, db_engine):
        SessionLocal = sessionmaker(bind=db_engine)
        session = SessionLocal()

        for i in range(5):
            _create_requirement(
                session,
                req_id=f"REQ-20260705-{i+1:03d}",
                status="PENDING_REVIEW",
                stage="review",
            )
        session.close()

        def transition_req(req_id: str):
            s = SessionLocal()
            sm = StateMachine(s)
            result = sm.transition(req_id, Event.REVIEW_PASS)
            s.close()
            return result

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(transition_req, f"REQ-20260705-{i+1:03d}")
                for i in range(5)
            ]
            results = [f.result() for f in futures]

        assert all(r == Status.REVIEW_APPROVED for r in results)

        verify_session = SessionLocal()
        for i in range(5):
            req = verify_session.query(Requirements).filter_by(
                id=f"REQ-20260705-{i+1:03d}"
            ).first()
            assert req.current_status == "REVIEW_APPROVED"
        verify_session.close()


class TestEmptyTriggerUser:
    """Test S: FUNC/error — empty trigger_user accepted (system auto)."""

    def test_empty_trigger_user_accepted(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        result = state_machine.transition("REQ-20260705-001", Event.REVIEW_PASS, "")
        assert result == Status.REVIEW_APPROVED


class TestCanTransition:
    """Test can_transition method."""

    def test_can_transition_valid(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        assert state_machine.can_transition("REQ-20260705-001", Event.REVIEW_PASS) is True

    def test_can_transition_invalid(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        assert state_machine.can_transition("REQ-20260705-001", Event.IMPL_CONFIRM) is False


class TestSaveState:
    """Test save_state method."""

    def test_save_state(self, db_session, state_machine):
        _create_requirement(db_session, status="PENDING_REVIEW", stage="review")
        state_machine.save_state("REQ-20260705-001", Status.DELIVERED)
        status = state_machine.get_status("REQ-20260705-001")
        assert status == Status.DELIVERED


class TestLoadStateNotFound:
    """Test load_state when requirement not found."""

    def test_load_state_not_found(self, state_machine):
        from app.core.state_machine import RequirementNotFoundError
        with pytest.raises(RequirementNotFoundError):
            state_machine.load_state("NONEXISTENT-001")
