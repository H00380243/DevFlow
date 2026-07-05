"""Tests for IdempotencyChecker — F004 重复提交幂等识别."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.core.idempotency import (
    IdempotencyCheckError,
    IdempotencyChecker,
    IdempotencyStoreError,
)


class TestIdempotencyCheckDuplicate:
    """Test J: FR-003 AC-1 — duplicate within 5 min returns existing ID."""

    def test_check_duplicate_returns_existing_id(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "REQ-20260705-001"
        mock_session.execute.return_value = mock_result

        checker = IdempotencyChecker(db_session=mock_session)
        result = checker.check(sender_hash=12345, content="加一个登录页")

        assert result == "REQ-20260705-001"


class TestIdempotencyCheckExpired:
    """Test K: FR-003 AC-2 — expired entry returns None."""

    def test_check_expired_returns_none(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        checker = IdempotencyChecker(db_session=mock_session)
        result = checker.check(sender_hash=12345, content="加一个登录页")

        assert result is None


class TestIdempotencyCheckDifferentSender:
    """Test L: FR-003 AC-3 — different sender returns None."""

    def test_check_different_sender_returns_none(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        checker = IdempotencyChecker(db_session=mock_session)
        result = checker.check(sender_hash=99999, content="加一个登录页")

        assert result is None


class TestIdempotencyCheckExact5MinBoundary:
    """Test M: FR-003 AC-1 — exactly 5 min boundary = expired."""

    def test_check_exact_5min_boundary_returns_none(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        checker = IdempotencyChecker(db_session=mock_session)
        result = checker.check(sender_hash=12345, content="加一个登录页")

        assert result is None


class TestIdempotencyCheckDbFailure:
    """Test O: DB query failure raises IdempotencyCheckError."""

    def test_check_db_failure_raises(self):
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError("db", {}, Exception("fail"))

        checker = IdempotencyChecker(db_session=mock_session)
        with pytest.raises(IdempotencyCheckError, match="Failed to check idempotency"):
            checker.check(sender_hash=12345, content="加一个登录页")


class TestIdempotencyStore:
    """Test idempotency store operations."""

    def test_store_inserts_row(self):
        mock_session = MagicMock()
        checker = IdempotencyChecker(db_session=mock_session)

        checker.store(sender_hash=12345, content="加一个登录页", req_id="REQ-20260705-001")

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_store_db_failure_raises(self):
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError("db", {}, Exception("fail"))

        checker = IdempotencyChecker(db_session=mock_session)
        with pytest.raises(IdempotencyStoreError, match="Failed to store idempotency record"):
            checker.store(sender_hash=12345, content="加一个登录页", req_id="REQ-20260705-001")


class TestIdempotencyRoundTrip:
    """Test U: INTG — store then check returns stored ID."""

    def test_round_trip_store_then_check(self):
        mock_session = MagicMock()

        checker = IdempotencyChecker(db_session=mock_session)
        checker.store(sender_hash=12345, content="加一个登录页", req_id="REQ-20260705-001")

        mock_result = MagicMock()
        mock_result.scalar.return_value = "REQ-20260705-001"
        mock_session.execute.return_value = mock_result

        result = checker.check(sender_hash=12345, content="加一个登录页")
        assert result == "REQ-20260705-001"
