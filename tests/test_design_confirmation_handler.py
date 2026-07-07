"""Tests for DesignConfirmationHandler — F014 设计确认门与迭代."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Requirements, StatusHistory


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
def req_design_pending_confirm(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260708-001",
        original_text="测试需求",
        summary="测试",
        submitter_id="user001",
        current_stage="design",
        current_status="DESIGN_PENDING_CONFIRM",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


@pytest.fixture
def push_fn():
    return MagicMock()


@pytest.fixture
def design_team_fn():
    return MagicMock()


@pytest.fixture
def handler(db_session, push_fn, design_team_fn):
    from app.core.design_confirmation_handler import DesignConfirmationHandler
    return DesignConfirmationHandler(
        session=db_session,
        push_fn=push_fn,
        design_team_fn=design_team_fn,
    )


@pytest.fixture
def timeout_monitor(db_session, push_fn, handler):
    from app.core.design_confirmation_handler import ConfirmationTimeoutMonitor
    return ConfirmationTimeoutMonitor(
        session=db_session,
        push_fn=push_fn,
        handler=handler,
    )


# ----- Happy Paths -----


class TestHandleConfirm:
    """T001: FUNC/happy — confirm design, transition to IN_IMPLEMENTATION."""

    def test_handle_confirm_success(self, handler, req_design_pending_confirm, push_fn):
        from app.core.state_machine import Status
        handler.handle_confirm("REQ-20260708-001", "user001")
        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.IN_IMPLEMENTATION
        push_fn.assert_called_once()
        assert "已确认" in push_fn.call_args[0][1]


class TestStartConfirmationGate:
    """T002: FUNC/happy — start confirmation gate pushes design link."""

    def test_start_confirmation_gate(self, handler, req_design_pending_confirm, push_fn):
        handler.start_confirmation_gate("REQ-20260708-001", "http://design/doc", "user001")
        push_fn.assert_called_once()
        assert "确认" in push_fn.call_args[0][1] or "驳回" in push_fn.call_args[0][1]


class TestHandleRejectWithReason:
    """T003: FUNC/happy — reject with reason re-triggers design team."""

    def test_handle_reject_with_reason(self, handler, req_design_pending_confirm, push_fn, design_team_fn):
        from app.core.state_machine import Status
        handler.handle_reject("REQ-20260708-001", "user001", "需要修改接口")
        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.IN_DESIGN
        assert design_team_fn.call_count >= 1
        push_fn_calls = [c for c in push_fn.call_args_list if "已驳回" in c[0][1]]
        assert len(push_fn_calls) >= 1


class TestHandleConfirmLeadsToImplementation:
    """T004: FUNC/happy — confirm leads to IN_IMPLEMENTATION."""

    def test_handle_confirm_implementation(self, handler, req_design_pending_confirm):
        from app.core.state_machine import Status
        handler.handle_confirm("REQ-20260708-001", "user001")
        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.IN_IMPLEMENTATION


# ----- Error Paths -----


class TestPushRetry:
    """T005: FUNC/error — push fails 3 times, raises NotificationFailedError."""

    def test_push_retry_fails(self, handler, req_design_pending_confirm, push_fn):
        from app.core.arbitration_notification import NotificationFailedError
        push_fn.side_effect = IOError("push failed")
        with pytest.raises(NotificationFailedError):
            handler._push_with_retry("user001", "test message")
        assert push_fn.call_count == 3


class TestRejectWithEmptyReason:
    """T006: FUNC/error — empty reason raises EmptyRejectReasonError."""

    def test_reject_empty_reason(self, handler, req_design_pending_confirm, push_fn):
        from app.core.design_confirmation_handler import EmptyRejectReasonError
        with pytest.raises(EmptyRejectReasonError) as excinfo:
            handler.handle_reject("REQ-20260708-001", "user001", "")
        assert "修改意见" in str(excinfo.value)
        push_fn_calls = [c for c in push_fn.call_args_list if "修改意见" in c[0][1]]
        assert len(push_fn_calls) >= 1


class TestRejectWithNoneReason:
    """T007: FUNC/error — None reason raises EmptyRejectReasonError."""

    def test_reject_none_reason(self, handler, req_design_pending_confirm, push_fn):
        from app.core.design_confirmation_handler import EmptyRejectReasonError
        with pytest.raises(EmptyRejectReasonError):
            handler.handle_reject("REQ-20260708-001", "user001", None)


class TestPermissionCheckNonSubmitter:
    """T008: FUNC/error — non-submitter rejected by CommandExecutor."""

    def test_non_submitter_rejected(self, db_session, req_design_pending_confirm):
        from app.core.command_executor import CommandExecutor
        from app.core.state_machine import StateMachine
        handler = MagicMock()
        executor = CommandExecutor(
            state_machine=StateMachine(db_session),
            design_confirmation_handler=handler,
        )
        result = executor.execute(
            "user999", "确认 REQ-20260708-001", db_session
        )
        assert result.status == "error"
        assert "无权限" in result.message


class TestInvalidStateConfirm:
    """T009: FUNC/error — confirm on DESIGN_REJECTED state raises error."""

    def test_invalid_state_confirm(self, handler, req_design_pending_confirm):
        from app.core.state_machine import InvalidTransitionError, Status
        handler._sm.save_state("REQ-20260708-001", Status.DESIGN_REJECTED)
        with pytest.raises(InvalidTransitionError):
            handler.handle_confirm("REQ-20260708-001", "user001")


class TestMissingRequirement:
    """T010: FUNC/error — requirement not found raises error."""

    def test_missing_requirement(self, handler):
        from app.core.state_machine import RequirementNotFoundError
        with pytest.raises(RequirementNotFoundError):
            handler.handle_confirm("REQ-NONEXIST-001", "user001")


class TestCommandExecutorRoutingConfirm:
    """T011: FUNC/happy — CommandExecutor routes confirm to handler."""

    def test_routing_confirm(self, db_session, req_design_pending_confirm):
        from app.core.command_executor import CommandExecutor
        from app.core.state_machine import StateMachine
        handler_mock = MagicMock()
        executor = CommandExecutor(
            state_machine=StateMachine(db_session),
            design_confirmation_handler=handler_mock,
        )
        result = executor.execute(
            "user001", "确认 REQ-20260708-001", db_session
        )
        handler_mock.handle_confirm.assert_called_once_with(
            "REQ-20260708-001", "user001"
        )
        assert result.status == "ok"


class TestCommandExecutorRoutingReject:
    """T012: FUNC/happy — CommandExecutor routes reject to handler."""

    def test_routing_reject(self, db_session, req_design_pending_confirm):
        from app.core.command_executor import CommandExecutor
        from app.core.state_machine import StateMachine
        handler_mock = MagicMock()
        executor = CommandExecutor(
            state_machine=StateMachine(db_session),
            design_confirmation_handler=handler_mock,
        )
        result = executor.execute(
            "user001", "驳回 REQ-20260708-001 接口不完整", db_session
        )
        handler_mock.handle_reject.assert_called_once_with(
            "REQ-20260708-001", "user001", "接口不完整"
        )
        assert result.status == "ok"


# ----- Boundary Tests -----


class TestRetryCountBoundaryThreeRejects:
    """T013: BNDRY/edge — 3rd reject triggers TERMINATED."""

    def test_three_rejects_terminated(self, handler, req_design_pending_confirm, push_fn, design_team_fn):
        from app.core.state_machine import Status, Event
        design_team_fn.reset_mock()
        push_fn.reset_mock()
        for _ in range(3):
            handler._sm.transition("REQ-20260708-001", Event.DESIGN_REJECT, "user001")
            handler._sm.transition("REQ-20260708-001", Event.DESIGN_RETRY, None)
            handler._sm.transition("REQ-20260708-001", Event.DESIGN_COMPLETE, None)
        handler.handle_reject("REQ-20260708-001", "user001", "again")
        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.TERMINATED
        admin_calls = [c for c in push_fn.call_args_list if "admin" in c[0][0] or "管理员" in c[0][1]]
        assert len(admin_calls) >= 1


class TestTimeoutCountBoundaryTwoReminder:
    """T014: BNDRY/edge — 2 timeouts sends reminder, not escalation."""

    def test_timeout_two_reminds(self, handler, req_design_pending_confirm, push_fn, timeout_monitor):
        from app.core.state_machine import Event
        handler._sm.transition("REQ-20260708-001", Event.TIMEOUT, None)
        now = datetime.now(timezone.utc)
        results = timeout_monitor.check_timeouts(now + timedelta(hours=5))
        assert len(results) >= 1
        escalated = [r for r in results if r.escalated]
        assert len(escalated) == 0


class TestTimeoutCountBoundaryThreeEscalation:
    """T015: BNDRY/edge — 3 timeouts triggers escalation to admin."""

    def test_timeout_three_escalates(self, handler, req_design_pending_confirm, push_fn, timeout_monitor):
        from app.core.state_machine import Event
        for _ in range(3):
            handler._sm.transition("REQ-20260708-001", Event.TIMEOUT, None)
        now = datetime.now(timezone.utc)
        results = timeout_monitor.check_timeouts(now + timedelta(hours=5))
        escalated = [r for r in results if r.escalated]
        assert len(escalated) >= 1


class TestRetryCountBoundaryFirstReject:
    """T016: BNDRY/edge — first reject triggers re-design, not terminate."""

    def test_first_reject_redesign(self, handler, req_design_pending_confirm, design_team_fn):
        from app.core.state_machine import Status
        handler.handle_reject("REQ-20260708-001", "user001", "需要修改")
        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.IN_DESIGN


class TestRejectWithWhitespaceReason:
    """T017: BNDRY/edge — whitespace-only reason raises error."""

    def test_reject_whitespace_reason(self, handler, req_design_pending_confirm, push_fn):
        from app.core.design_confirmation_handler import EmptyRejectReasonError
        with pytest.raises(EmptyRejectReasonError):
            handler.handle_reject("REQ-20260708-001", "user001", "   ")


class TestTimeoutExactBoundary:
    """T018: BNDRY/edge — exactly 4h ago is included in timeout check."""

    def test_timeout_exactly_4h(self, handler, req_design_pending_confirm, push_fn, timeout_monitor):
        now = datetime.now(timezone.utc)
        four_hours_ago = now - timedelta(hours=4)
        req_design_pending_confirm.updated_at = four_hours_ago
        timeout_monitor._session.commit()
        results = timeout_monitor.check_timeouts(now)
        assert len(results) >= 1


# ----- State Tests -----


class TestDoubleConfirmInvalid:
    """T019: FUNC/state — DESIGN_REJECTED + confirm is invalid."""

    def test_double_confirm_invalid(self, handler, req_design_pending_confirm):
        from app.core.state_machine import InvalidTransitionError, Status
        handler._sm.save_state("REQ-20260708-001", Status.DESIGN_REJECTED)
        with pytest.raises(InvalidTransitionError):
            handler.handle_confirm("REQ-20260708-001", "user001")


class TestTerminatedRejectInvalid:
    """T020: FUNC/state — TERMINATED + reject is invalid."""

    def test_terminated_reject_invalid(self, handler, req_design_pending_confirm):
        from app.core.state_machine import InvalidTransitionError, Status
        handler._sm.save_state("REQ-20260708-001", Status.TERMINATED)
        with pytest.raises(InvalidTransitionError):
            handler.handle_reject("REQ-20260708-001", "user001", "too late")


# ----- Integration Tests -----


class TestConfirmPersistsToDb:
    """T021: INTG/db — confirm persists state change."""

    def test_confirm_persists(self, db_session, req_design_pending_confirm, push_fn, design_team_fn, db_engine):
        from app.core.design_confirmation_handler import DesignConfirmationHandler
        h = DesignConfirmationHandler(
            session=db_session, push_fn=push_fn, design_team_fn=design_team_fn
        )
        h.handle_confirm("REQ-20260708-001", "user001")
        SessionLocal = sessionmaker(bind=db_engine)
        fresh_session = SessionLocal()
        try:
            row = fresh_session.execute(
                text("SELECT current_status FROM requirements WHERE id = 'REQ-20260708-001'")
            ).first()
            assert row.current_status == "IN_IMPLEMENTATION"
        finally:
            fresh_session.close()


class TestRejectPersistsToDb:
    """T022: INTG/db — reject persists state change."""

    def test_reject_persists(self, db_session, req_design_pending_confirm, push_fn, design_team_fn, db_engine):
        from app.core.design_confirmation_handler import DesignConfirmationHandler
        h = DesignConfirmationHandler(
            session=db_session, push_fn=push_fn, design_team_fn=design_team_fn
        )
        h.handle_reject("REQ-20260708-001", "user001", "改动")
        SessionLocal = sessionmaker(bind=db_engine)
        fresh_session = SessionLocal()
        try:
            row = fresh_session.execute(
                text("SELECT current_status FROM requirements WHERE id = 'REQ-20260708-001'")
            ).first()
            assert row.current_status == "IN_DESIGN"
        finally:
            fresh_session.close()


class TestTimeoutPersistsToDb:
    """T023: INTG/db — timeout counter persists."""

    def test_timeout_persists(self, handler, req_design_pending_confirm, push_fn, db_engine, timeout_monitor):
        from app.core.state_machine import Event
        handler._sm.transition("REQ-20260708-001", Event.TIMEOUT, None)
        now = datetime.now(timezone.utc)
        timeout_monitor.check_timeouts(now + timedelta(hours=5))
        SessionLocal = sessionmaker(bind=db_engine)
        fresh_session = SessionLocal()
        try:
            rows = fresh_session.execute(
                text(
                    "SELECT COUNT(*) as cnt FROM status_history "
                    "WHERE requirement_id = 'REQ-20260708-001' AND trigger_event = 'TIMEOUT'"
                )
            ).first()
            assert rows.cnt >= 2
        finally:
            fresh_session.close()


class TestMaxRetryPersistsToDb:
    """T024: INTG/db — MAX_RETRY on 3rd reject persists."""

    def test_max_retry_persists(self, handler, req_design_pending_confirm, push_fn, design_team_fn, db_engine):
        from app.core.state_machine import Status, Event
        design_team_fn.reset_mock()
        push_fn.reset_mock()
        for _ in range(3):
            handler._sm.transition("REQ-20260708-001", Event.DESIGN_REJECT, "user001")
            handler._sm.transition("REQ-20260708-001", Event.DESIGN_RETRY, None)
            handler._sm.transition("REQ-20260708-001", Event.DESIGN_COMPLETE, None)
        handler.handle_reject("REQ-20260708-001", "user001", "第四次")
        SessionLocal = sessionmaker(bind=db_engine)
        fresh_session = SessionLocal()
        try:
            row = fresh_session.execute(
                text("SELECT current_status FROM requirements WHERE id = 'REQ-20260708-001'")
            ).first()
            assert row.current_status == "TERMINATED"
        finally:
            fresh_session.close()


class TestRejectDirectlyToTerminated:
    """T025: FUNC/branch — handle_reject when state machine returns TERMINATED directly."""

    def test_reject_directly_terminated(self, handler, req_design_pending_confirm, push_fn, design_team_fn):
        from unittest.mock import patch
        from app.core.state_machine import Status
        with patch.object(handler._sm, "transition", return_value=Status.TERMINATED):
            handler.handle_reject("REQ-20260708-001", "user001", "超时终止")
        push_fn.assert_called()
        call_args = [str(c) for c in push_fn.call_args_list]
        assert any("admin" in c for c in call_args)


class TestStartConfirmationGateWrongStatus:
    """T026: FUNC/branch — start_confirmation_gate returns early if status is wrong."""

    def test_wrong_status_no_push(self, handler, req_design_pending_confirm, push_fn, db_session):
        from app.core.state_machine import Event
        handler._sm.transition("REQ-20260708-001", Event.DESIGN_CONFIRM, "user001")
        push_fn.reset_mock()
        handler.start_confirmation_gate("REQ-20260708-001", "http://doc", "user001")
        push_fn.assert_not_called()
