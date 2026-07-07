"""Tests for ImplementationConfirmationHandler — F017 实施确认门."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.arbitration_notification import NotificationFailedError
from app.core.implementation_confirmation_handler import (
    ConfirmationTimeoutMonitor,
    EmptyRejectReasonError,
    ImplementationConfirmationHandler,
)
from app.core.state_machine import Event, StateMachine, Status
from app.models import Base, Requirements


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    req = Requirements(
        id="REQ-20260709-001",
        original_text="test requirement",
        summary="test",
        submitter_id="user-A",
        submitter_name="User A",
        current_stage="implementation",
        current_status=Status.IMPL_PENDING_ACCEPTANCE.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    s.add(req)
    s.commit()
    yield s
    s.close()


@pytest.fixture
def push_fn():
    return MagicMock()


@pytest.fixture
def implementation_fn():
    return MagicMock()


@pytest.fixture
def handler(session, push_fn, implementation_fn):
    return ImplementationConfirmationHandler(
        session=session, push_fn=push_fn, implementation_team_fn=implementation_fn,
    )


class TestStartConfirmationGate:
    def test_start_confirmation_gate_success(self, session, handler, push_fn):
        handler.start_confirmation_gate(
            "REQ-20260709-001",
            {"syntax_ok": True, "imports_ok": True, "startup_ok": True},
            "user-A",
        )
        push_fn.assert_called_once()
        args, _ = push_fn.call_args
        assert "REQ-20260709-001" in args[1]
        assert "REQ-20260709-001" in args[1]

    def test_start_confirmation_gate_wrong_state(self, session, handler, push_fn):
        session.execute(
            text("UPDATE requirements SET current_status = :st WHERE id = :id"),
            {"st": Status.IN_IMPLEMENTATION.value, "id": "REQ-20260709-001"},
        )
        session.commit()
        handler.start_confirmation_gate(
            "REQ-20260709-001",
            {"syntax_ok": True, "imports_ok": True, "startup_ok": True},
            "user-A",
        )
        push_fn.assert_not_called()


class TestHandleConfirm:
    def test_handle_confirm_success(self, session, handler, push_fn):
        result = handler.handle_confirm("REQ-20260709-001", "user-A")
        assert result == Status.DELIVERED
        push_fn.assert_called_once()

    def test_handle_confirm_invalid_state(self, session, handler, push_fn):
        session.execute(
            text("UPDATE requirements SET current_status = :st WHERE id = :id"),
            {"st": Status.DELIVERED.value, "id": "REQ-20260709-001"},
        )
        session.commit()
        with pytest.raises(Exception):
            handler.handle_confirm("REQ-20260709-001", "user-A")

    def test_handle_confirm_nonexistent(self, handler, push_fn):
        from app.core.state_machine import RequirementNotFoundError

        with pytest.raises(RequirementNotFoundError):
            handler.handle_confirm("REQ-99999999-999", "user-A")


class TestHandleReject:
    def test_handle_reject_with_reason(self, session, handler, push_fn, implementation_fn):
        result = handler.handle_reject("REQ-20260709-001", "user-A", "需要优化")
        assert result == Status.IN_IMPLEMENTATION
        implementation_fn.assert_called_once()
        push_fn.assert_called_once()

    def test_handle_reject_empty_reason(self, handler, push_fn):
        with pytest.raises(EmptyRejectReasonError):
            handler.handle_reject("REQ-20260709-001", "user-A", "")

    def test_handle_reject_none_reason(self, handler, push_fn):
        with pytest.raises(EmptyRejectReasonError):
            handler.handle_reject("REQ-20260709-001", "user-A", None)

    def test_handle_reject_max_retry(self, session, handler, push_fn, implementation_fn):
        for _ in range(3):
            session.execute(
                text(
                    "INSERT INTO status_history (requirement_id, from_status, to_status, "
                    "trigger_event, trigger_user, triggered_at) VALUES "
                    "(:rid, :fs, :ts, :ev, :usr, :now)"
                ),
                {
                    "rid": "REQ-20260709-001",
                    "fs": Status.IMPL_REJECTED.value,
                    "ts": Status.IN_IMPLEMENTATION.value,
                    "ev": "IMPL_RETRY",
                    "usr": "user-A",
                    "now": datetime.now(timezone.utc),
                },
            )
        session.commit()
        result = handler.handle_reject("REQ-20260709-001", "user-A", "test")
        assert result == Status.TERMINATED
        implementation_fn.assert_not_called()
        push_fn.assert_called()
        call_args = push_fn.call_args_list[-1]
        assert "达3轮" in call_args[0][1]

    def test_handle_reject_first_retry(self, session, handler, push_fn, implementation_fn):
        """T015: first reject triggers redesign."""
        result = handler.handle_reject("REQ-20260709-001", "user-A", "需优化")
        assert result == Status.IN_IMPLEMENTATION
        implementation_fn.assert_called_once()


class TestPushRetry:
    def test_push_retry_exhausted(self, session, push_fn):
        push_fn.side_effect = ConnectionError("fail")
        handler = ImplementationConfirmationHandler(
            session=session, push_fn=push_fn,
            implementation_team_fn=MagicMock(),
        )
        with pytest.raises(NotificationFailedError):
            handler._push_with_retry("user-A", "test")

    def test_push_retry_recover_second(self, session, push_fn):
        call_count = 0

        def flaky_push(recipient, msg):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")

        push_fn.side_effect = flaky_push
        handler = ImplementationConfirmationHandler(
            session=session, push_fn=push_fn,
            implementation_team_fn=MagicMock(),
        )
        handler._push_with_retry("user-A", "test")
        assert call_count == 2


class TestTimeoutMonitor:
    @pytest.fixture
    def old_session(self, session):
        session.execute(
            text("UPDATE requirements SET updated_at = :dt WHERE id = :id"),
            {
                "dt": datetime.now(timezone.utc) - timedelta(hours=5),
                "id": "REQ-20260709-001",
            },
        )
        session.commit()
        return session

    def test_timeout_reminder(self, old_session, push_fn):
        monitor = ConfirmationTimeoutMonitor(
            session=old_session, push_fn=push_fn,
        )
        results = monitor.check_timeouts()
        assert len(results) == 1
        assert results[0].escalated is False
        push_fn.assert_called_once()
        assert "实施确认" in push_fn.call_args[0][1]

    def test_timeout_escalation(self, session, push_fn):
        session.execute(
            text("UPDATE requirements SET updated_at = :dt WHERE id = :id"),
            {
                "dt": datetime.now(timezone.utc) - timedelta(hours=5),
                "id": "REQ-20260709-001",
            },
        )
        session.commit()
        for _ in range(3):
            session.execute(
                text(
                    "INSERT INTO status_history (requirement_id, from_status, to_status, "
                    "trigger_event, trigger_user, triggered_at) VALUES "
                    "(:rid, :fs, :ts, :ev, :usr, :now)"
                ),
                {
                    "rid": "REQ-20260709-001",
                    "fs": Status.IMPL_PENDING_ACCEPTANCE.value,
                    "ts": Status.IMPL_PENDING_ACCEPTANCE.value,
                    "ev": "TIMEOUT",
                    "usr": None,
                    "now": datetime.now(timezone.utc),
                },
            )
        session.commit()
        monitor = ConfirmationTimeoutMonitor(
            session=session, push_fn=push_fn,
        )
        results = monitor.check_timeouts()
        assert len(results) == 1
        assert results[0].escalated is True
        push_fn.assert_called_once()
        assert "升级" in push_fn.call_args[0][1]

    def test_timeout_no_overdue(self, session, push_fn):
        session.execute(
            text("UPDATE requirements SET updated_at = :dt WHERE id = :id"),
            {"dt": datetime.now(timezone.utc), "id": "REQ-20260709-001"},
        )
        session.commit()
        monitor = ConfirmationTimeoutMonitor(
            session=session, push_fn=push_fn,
        )
        results = monitor.check_timeouts()
        assert results == []

    def test_timeout_db_failure(self, session, push_fn):
        bad_session = MagicMock()
        bad_session.execute.side_effect = Exception("DB down")
        monitor = ConfirmationTimeoutMonitor(
            session=bad_session, push_fn=push_fn,
        )
        results = monitor.check_timeouts()
        assert results == []

    def test_timeout_count_boundary(self, session, push_fn):
        session.execute(
            text("UPDATE requirements SET updated_at = :dt WHERE id = :id"),
            {
                "dt": datetime.now(timezone.utc) - timedelta(hours=5),
                "id": "REQ-20260709-001",
            },
        )
        session.commit()
        for _ in range(2):
            session.execute(
                text(
                    "INSERT INTO status_history (requirement_id, from_status, to_status, "
                    "trigger_event, trigger_user, triggered_at) VALUES "
                    "(:rid, :fs, :ts, :ev, :usr, :now)"
                ),
                {
                    "rid": "REQ-20260709-001",
                    "fs": Status.IMPL_PENDING_ACCEPTANCE.value,
                    "ts": Status.IMPL_PENDING_ACCEPTANCE.value,
                    "ev": "TIMEOUT",
                    "usr": None,
                    "now": datetime.now(timezone.utc),
                },
            )
        session.commit()
        monitor = ConfirmationTimeoutMonitor(
            session=session, push_fn=push_fn,
        )
        results = monitor.check_timeouts()
        assert len(results) == 1
        assert results[0].escalated is False

    def test_timeout_count_boundary_escalation(self, session, push_fn):
        session.execute(
            text("UPDATE requirements SET updated_at = :dt WHERE id = :id"),
            {
                "dt": datetime.now(timezone.utc) - timedelta(hours=5),
                "id": "REQ-20260709-001",
            },
        )
        session.commit()
        for _ in range(3):
            session.execute(
                text(
                    "INSERT INTO status_history (requirement_id, from_status, to_status, "
                    "trigger_event, trigger_user, triggered_at) VALUES "
                    "(:rid, :fs, :ts, :ev, :usr, :now)"
                ),
                {
                    "rid": "REQ-20260709-001",
                    "fs": Status.IMPL_PENDING_ACCEPTANCE.value,
                    "ts": Status.IMPL_PENDING_ACCEPTANCE.value,
                    "ev": "TIMEOUT",
                    "usr": None,
                    "now": datetime.now(timezone.utc),
                },
            )
        session.commit()
        monitor = ConfirmationTimeoutMonitor(
            session=session, push_fn=push_fn,
        )
        results = monitor.check_timeouts()
        assert len(results) == 1
        assert results[0].escalated is True
