"""Tests for ArbitrationNotifier & ArbitrationTimeoutMonitor & CommandExecutor arbitration routing — F010 人工仲裁处理."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.core.arbitration_notification import (
    ESCALATION_THRESHOLD,
    MAX_RETRIES,
    TIMEOUT_HOURS,
    ArbitrationNotifier,
    ArbitrationTimeoutMonitor,
    NotificationFailedError,
    TimeoutResult,
)
from app.core.command_executor import CommandExecutor, CommandResult
from app.core.state_machine import Event, Status, RequirementNotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_push():
    return MagicMock()


@pytest.fixture
def notifier(mock_push):
    return ArbitrationNotifier(push_fn=mock_push)


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_state_machine():
    return MagicMock()


@pytest.fixture
def mock_arbitration_handler():
    return MagicMock()


@pytest.fixture
def executor_with_arbitration(mock_state_machine, mock_arbitration_handler):
    return CommandExecutor(
        state_machine=mock_state_machine,
        arbitration_handler=mock_arbitration_handler,
    )


# ---------------------------------------------------------------------------
# Helper: make mock DB row
# ---------------------------------------------------------------------------

def _make_row(mapping: dict) -> MagicMock:
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: mapping[key]
    mock_row._mapping = mapping
    return mock_row


# ===========================================================
# A: FUNC/happy — notify_admin success
# ===========================================================

class TestNotifyAdminHappyPath:
    """Test A: FUNC/happy — push succeeds on first call."""

    def test_notify_admin_success(self, notifier, mock_push):
        notifier.notify_admin("REQ-20260707-001", "评审详情摘要")

        mock_push.assert_called_once_with(
            "REQ-20260707-001", "评审详情摘要"
        )


# ===========================================================
# B: FUNC/happy — notify_admin passes req_id and summary
# ===========================================================

class TestNotifyAdminContent:
    """Test B: verify message content contains req_id and summary."""

    def test_notify_admin_content(self, notifier, mock_push):
        notifier.notify_admin("REQ-20260707-001", "评审详情摘要：业务价值2分")

        mock_push.assert_called_once()
        args, _ = mock_push.call_args
        assert args[0] == "REQ-20260707-001"
        assert "评审详情摘要" in args[1]


# ===========================================================
# C: "确认" routes to arbitration when PENDING_ARBITRATION
# ===========================================================

class TestConfirmRoutesToArbitration:
    """Test C: FUNC/happy — confirm command routes to arbitration handle_response."""

    def test_confirm_routes_to_arbitration(
        self, executor_with_arbitration, mock_state_machine, mock_arbitration_handler
    ):
        mock_state_machine.get_status.return_value = Status.PENDING_ARBITRATION
        mock_arbitration_handler.handle_response.return_value = Status.REVIEW_APPROVED

        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})
        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260707-001"})
        mock_db.execute.side_effect = [mock_check_result, mock_req_result]

        result = executor_with_arbitration.execute(
            "user1", "确认 REQ-20260707-001", mock_db
        )

        assert result.status == "ok"
        mock_arbitration_handler.handle_response.assert_called_once_with(
            req_id="REQ-20260707-001",
            approved=True,
            reason="",
            admin_id="user1",
        )


# ===========================================================
# D: "驳回" routes to arbitration when PENDING_ARBITRATION
# ===========================================================

class TestRejectRoutesToArbitration:
    """Test D: FUNC/happy — reject command routes to arbitration handle_response."""

    def test_reject_routes_to_arbitration(
        self, executor_with_arbitration, mock_state_machine, mock_arbitration_handler
    ):
        mock_state_machine.get_status.return_value = Status.PENDING_ARBITRATION
        mock_arbitration_handler.handle_response.return_value = Status.REJECTED

        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})
        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260707-001"})
        mock_db.execute.side_effect = [mock_check_result, mock_req_result]

        result = executor_with_arbitration.execute(
            "user1", "驳回 REQ-20260707-001 理由不充分", mock_db
        )

        assert result.status == "ok"
        mock_arbitration_handler.handle_response.assert_called_once_with(
            req_id="REQ-20260707-001",
            approved=False,
            reason="理由不充分",
            admin_id="user1",
        )


# ===========================================================
# E: notify_admin 3 failures → NotificationFailedError
# ===========================================================

class TestNotifyAdminAllRetriesFail:
    """Test E: FUNC/error — 3 consecutive failures raises NotificationFailedError."""

    def test_all_retries_fail(self, notifier, mock_push):
        mock_push.side_effect = ConnectionError("IM timeout")

        with pytest.raises(NotificationFailedError) as excinfo:
            notifier.notify_admin("REQ-20260707-001", "摘要")

        assert str(MAX_RETRIES) in str(excinfo.value)
        assert mock_push.call_count == MAX_RETRIES


# ===========================================================
# F: notify_admin fails twice, 3rd succeeds
# ===========================================================

class TestNotifyAdminRecoverOnThirdRetry:
    """Test F: FUNC/happy — first 2 fail, 3rd succeeds."""

    def test_recover_on_third_retry(self, notifier, mock_push):
        mock_push.side_effect = [
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            None,
        ]

        notifier.notify_admin("REQ-20260707-001", "摘要")

        assert mock_push.call_count == 3


# ===========================================================
# G: check_timeouts — timeout_count 0 → reminder
# ===========================================================

class TestCheckTimeoutsReminder:
    """Test G: FUNC/happy — overdue request gets IM reminder, timeout_count incremented."""

    def test_reminder_sent(self, mock_db_session, notifier):
        mock_req = MagicMock()
        mock_req.requirement_id = "REQ-20260707-001"
        mock_req.timeout_count = 0
        mock_req.requested_at = datetime.now(timezone.utc) - timedelta(hours=TIMEOUT_HOURS + 1)

        query_mock = MagicMock()
        query_mock.all.return_value = [mock_req]
        mock_db_session.query.return_value.filter.return_value = query_mock

        monitor = ArbitrationTimeoutMonitor(mock_db_session, notifier)
        results = monitor.check_timeouts()

        assert len(results) == 1
        assert results[0].req_id == "REQ-20260707-001"
        assert results[0].timeout_count == 1
        assert results[0].escalated is False
        mock_db_session.commit.assert_called_once()


# ===========================================================
# H: check_timeouts — boundary 2→3 (timeout_count=2 → becomes 3, no escalation)
# ===========================================================

class TestCheckTimeoutsBoundaryTwoToThree:
    """Test H: BNDRY/edge — timeout_count=2 increments to 3, NOT escalated yet."""

    def test_boundary_two_to_three(self, mock_db_session, notifier):
        mock_req = MagicMock()
        mock_req.requirement_id = "REQ-20260707-001"
        mock_req.timeout_count = 2
        mock_req.requested_at = datetime.now(timezone.utc) - timedelta(hours=TIMEOUT_HOURS + 1)

        query_mock = MagicMock()
        query_mock.all.return_value = [mock_req]
        mock_db_session.query.return_value.filter.return_value = query_mock

        monitor = ArbitrationTimeoutMonitor(mock_db_session, notifier)
        results = monitor.check_timeouts()

        assert len(results) == 1
        assert results[0].timeout_count == 3
        # At 2→3, it's still a reminder, not escalation (>=3 for escalation, but this is the 3rd count)
        # Wait — ESCALATION_THRESHOLD = 3. When timeout_count = 2, 2 >= 3 is False, so it's a reminder
        assert results[0].escalated is False


# ===========================================================
# I: check_timeouts — timeout_count >= 3 → escalation
# ===========================================================

class TestCheckTimeoutsEscalation:
    """Test I: BNDRY/edge — timeout_count=3 triggers escalation."""

    def test_escalation_triggered(self, mock_db_session, notifier):
        mock_req = MagicMock()
        mock_req.requirement_id = "REQ-20260707-001"
        mock_req.timeout_count = 3
        mock_req.requested_at = datetime.now(timezone.utc) - timedelta(hours=TIMEOUT_HOURS + 1)

        query_mock = MagicMock()
        query_mock.all.return_value = [mock_req]
        mock_db_session.query.return_value.filter.return_value = query_mock

        monitor = ArbitrationTimeoutMonitor(mock_db_session, notifier)
        results = monitor.check_timeouts()

        assert len(results) == 1
        assert results[0].timeout_count == 3
        assert results[0].escalated is True


# ===========================================================
# J: check_timeouts — no overdue → empty list
# ===========================================================

class TestCheckTimeoutsNoOverdue:
    """Test J: BNDRY/edge — no overdue requests returns empty list."""

    def test_no_overdue(self, mock_db_session, notifier):
        query_mock = MagicMock()
        query_mock.all.return_value = []
        mock_db_session.query.return_value.filter.return_value = query_mock

        monitor = ArbitrationTimeoutMonitor(mock_db_session, notifier)
        results = monitor.check_timeouts()

        assert results == []


# ===========================================================
# K: "确认" on non-PENDING_ARBITRATION → normal flow
# ===========================================================

class TestConfirmNonArbitrationState:
    """Test K: FUNC/error — confirm on non-arbitration state falls through to normal flow."""

    def test_non_arbitration_state(
        self, executor_with_arbitration, mock_state_machine, mock_arbitration_handler
    ):
        mock_state_machine.get_status.return_value = Status.PENDING_REVIEW

        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})
        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260707-001"})
        mock_insert_result = MagicMock()
        mock_db.execute.side_effect = [
            mock_check_result,
            mock_req_result,
            mock_insert_result,
        ]

        result = executor_with_arbitration.execute(
            "user1", "确认 REQ-20260707-001", mock_db
        )

        assert result.status == "ok"
        assert "已确认" in result.message
        mock_arbitration_handler.handle_response.assert_not_called()


# ===========================================================
# L: "确认" on non-existent req → normal flow
# ===========================================================

class TestConfirmNonExistentRequirement:
    """Test L: FUNC/error — confirm on non-existent req does NOT call handle_response."""

    def test_non_existent_req(
        self, executor_with_arbitration, mock_state_machine, mock_arbitration_handler
    ):
        # Permission check returns False for non-existent req
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = None

        mock_db = MagicMock()
        mock_db.execute.return_value = mock_check_result

        result = executor_with_arbitration.execute(
            "user1", "确认 REQ-99999999-999", mock_db
        )

        assert result.status == "error"
        mock_arbitration_handler.handle_response.assert_not_called()


# ===========================================================
# M: notify_admin with empty summary
# ===========================================================

class TestNotifyAdminEmptySummary:
    """Test M: FUNC/error — empty summary is valid input, still sends."""

    def test_empty_summary(self, notifier, mock_push):
        notifier.notify_admin("REQ-20260707-001", "")

        mock_push.assert_called_once_with("REQ-20260707-001", "")


# ===========================================================
# N: check_timeouts — DB fails → empty list, no exception
# ===========================================================

class TestCheckTimeoutsDbFailure:
    """Test N: FUNC/error — DB query error returns empty list."""

    def test_db_failure(self, mock_db_session, notifier):
        mock_db_session.query.side_effect = Exception("DB connection lost")

        monitor = ArbitrationTimeoutMonitor(mock_db_session, notifier)
        results = monitor.check_timeouts()

        assert results == []
