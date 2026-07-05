"""Tests for PermissionChecker — F005 状态变更指令系统."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.core.permission_checker import PermissionCheckError, PermissionChecker


class TestCheckPermissionMatchesSubmitter:
    """Test: sender matches submitter_id → True."""

    def test_permission_granted(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = {"submitter_id": "user1"}
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        checker = PermissionChecker()
        assert checker.check_permission("user1", "REQ-20260705-001", mock_db) is True


class TestCheckPermissionMismatch:
    """Test: sender differs from submitter_id → False."""

    def test_permission_denied(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = {"submitter_id": "user1"}
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        checker = PermissionChecker()
        assert checker.check_permission("user2", "REQ-20260705-001", mock_db) is False


class TestCheckPermissionRequirementNotFound:
    """Test N: requirement doesn't exist → False."""

    def test_requirement_not_found(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        checker = PermissionChecker()
        assert checker.check_permission("user1", "REQ-99999999-999", mock_db) is False


class TestCheckPermissionDbFailure:
    """Test R: DB query failure raises PermissionCheckError."""

    def test_db_failure_raises(self):
        mock_db = MagicMock()
        mock_db.execute.side_effect = OperationalError("db", {}, Exception("fail"))

        checker = PermissionChecker()
        with pytest.raises(PermissionCheckError, match="Failed to check permission"):
            checker.check_permission("user1", "REQ-20260705-001", mock_db)
