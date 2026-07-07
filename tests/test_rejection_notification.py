"""Tests for RejectionNotifier and format_rejection_message — F011 评审驳回通知与归档."""

from unittest.mock import MagicMock

import pytest

from app.core.arbitration_notification import NotificationFailedError
from app.core.rejection_notification import RejectionNotifier, format_rejection_message
from app.core.review_aggregation import ArbitrationHandler
from app.core.state_machine import Event, Status


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_push():
    return MagicMock()


@pytest.fixture
def notifier(mock_push):
    return RejectionNotifier(push_fn=mock_push)


# ===========================================================
# A: FUNC/happy — notify_submitter success
# ===========================================================

class TestNotifySubmitterHappyPath:
    """Test A: FUNC/happy — push succeeds on first call, message contains key info."""

    def test_notify_submitter_success(self, notifier, mock_push):
        notifier.notify_submitter(
            "REQ-20260707-001", "方案不通过", "2角色反对"
        )

        mock_push.assert_called_once()
        args, _ = mock_push.call_args
        assert args[0] == "REQ-20260707-001"
        assert "REQ-20260707-001" in args[1]
        assert "方案不通过" in args[1]
        assert "2角色反对" in args[1]


# ===========================================================
# B: FUNC/happy — format_rejection_message format
# ===========================================================

class TestFormatRejectionMessage:
    """Test B: FUNC/happy — formatted message contains required Chinese headers."""

    def test_format_contains_required_fields(self):
        msg = format_rejection_message("REQ-001", "理由", "摘要")

        assert "需求编号" in msg
        assert "REQ-001" in msg
        assert "驳回原因" in msg
        assert "理由" in msg
        assert "评审摘要" in msg
        assert "摘要" in msg


# ===========================================================
# C: FUNC/happy — Notify recovers on 3rd retry
# ===========================================================

class TestNotifyRecoverOnThirdRetry:
    """Test C: FUNC/happy — first 2 fail, 3rd succeeds, no exception raised."""

    def test_recover_on_third_retry(self, notifier, mock_push):
        mock_push.side_effect = [
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            None,
        ]

        notifier.notify_submitter("REQ-001", "reason", "summary")

        assert mock_push.call_count == 3


# ===========================================================
# D: FUNC/error — Notify 3 failures → NotificationFailedError
# ===========================================================

class TestNotifyAllRetriesFail:
    """Test D: FUNC/error — 3 consecutive failures raises NotificationFailedError."""

    def test_all_retries_fail(self, notifier, mock_push):
        mock_push.side_effect = ConnectionError("IM timeout")

        with pytest.raises(NotificationFailedError) as excinfo:
            notifier.notify_submitter("REQ-001", "reason", "summary")

        assert "3" in str(excinfo.value)
        assert mock_push.call_count == 3


# ===========================================================
# E: FUNC/happy — handle_response(approved=False) → REJECTED
# ===========================================================

class TestHandleResponseRejected:
    """Test E: FUNC/happy — arbitration rejection transitions state to REJECTED."""

    def test_handle_response_rejected(self):
        mock_session = MagicMock()
        mock_sm = MagicMock()
        mock_sm.transition.return_value = Status.REJECTED

        mock_arb = MagicMock()
        mock_arb.requirement_id = "REQ-001"
        mock_arb.admin_response = None
        mock_arb.admin_id = None
        mock_arb.responded_at = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.side_effect = [mock_arb, None]
        mock_session.query.return_value = mock_query

        handler = ArbitrationHandler(session=mock_session, state_machine=mock_sm)
        result = handler.handle_response(
            req_id="REQ-001", approved=False, reason="理由不充分", admin_id="admin1"
        )

        assert result == Status.REJECTED
        mock_sm.transition.assert_called_once_with("REQ-001", Event.ARBITRATION_REJECT)


# ===========================================================
# F: FUNC/error — notify_submitter + commit failure (push failure retry)
# ===========================================================

class TestNotifySubmitterRetryExhaustion:
    """Test F: FUNC/error — all 3 push attempts fail, raises NotificationFailedError."""

    def test_all_retries_fail_raises_error(self, notifier, mock_push):
        mock_push.side_effect = RuntimeError("push failed")

        with pytest.raises(NotificationFailedError):
            notifier.notify_submitter("REQ-001", "reason", "summary")

        assert mock_push.call_count == 3


# ===========================================================
# G: BNDRY/edge — reason empty → fallback text
# ===========================================================

class TestReasonEmptyFallback:
    """Test G: BNDRY/edge — empty reason shows fallback '未提供原因'."""

    def test_empty_reason_fallback(self):
        msg = format_rejection_message("REQ-001", "", "摘要内容")
        assert "未提供原因" in msg

    def test_empty_reason_in_notification(self, notifier, mock_push):
        notifier.notify_submitter("REQ-001", "", "摘要内容")
        mock_push.assert_called_once()
        args, _ = mock_push.call_args
        assert "未提供原因" in args[1]
        assert "摘要内容" in args[1]


# ===========================================================
# H: BNDRY/edge — summary empty → fallback text
# ===========================================================

class TestSummaryEmptyFallback:
    """Test H: BNDRY/edge — empty summary shows fallback '无评审摘要'."""

    def test_empty_summary_fallback(self):
        msg = format_rejection_message("REQ-001", "理由不充分", "")
        assert "无评审摘要" in msg

    def test_empty_summary_in_notification(self, notifier, mock_push):
        notifier.notify_submitter("REQ-001", "理由不充分", "")
        mock_push.assert_called_once()
        args, _ = mock_push.call_args
        assert "无评审摘要" in args[1]
        assert "理由不充分" in args[1]
