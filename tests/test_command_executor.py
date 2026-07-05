"""Tests for CommandExecutor — F005 状态变更指令系统."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.core.command_executor import CommandExecutor, CommandResult
from app.core.command_parser import CommandParseError


def _make_row(mapping: dict) -> MagicMock:
    """Create a mock row that supports row._mapping[key] access."""
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: mapping[key]
    mock_row._mapping = mapping
    return mock_row


class TestExecuteConfirmHappyPath:
    """Test A: FUNC/happy — confirm command executed successfully."""

    def test_execute_confirm_ok(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260705-001"})

        mock_db.execute.side_effect = [mock_check_result, mock_req_result, MagicMock()]

        executor = CommandExecutor()
        result = executor.execute("user1", "确认 REQ-20260705-001", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "ok"
        assert "已确认 REQ-20260705-001" in result.message


class TestExecuteRejectHappyPath:
    """Test B: FUNC/happy — reject command with reason."""

    def test_execute_reject_with_reason(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260705-001"})

        mock_db.execute.side_effect = [mock_check_result, mock_req_result, MagicMock()]

        executor = CommandExecutor()
        result = executor.execute("user1", "驳回 REQ-20260705-001 逻辑不清", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "ok"
        assert "已驳回 REQ-20260705-001 逻辑不清" in result.message


class TestExecutePermissionDenied:
    """Test C: FUNC/error — wrong sender gets permission error."""

    def test_execute_permission_denied(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_db.execute.return_value = mock_check_result

        executor = CommandExecutor()
        result = executor.execute("user2", "确认 REQ-20260705-001", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"
        assert "无权限" in result.message


class TestExecuteRequirementNotFound:
    """Test D: FUNC/error — valid format but non-existent requirement."""

    def test_execute_requirement_not_found(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = None

        mock_db.execute.side_effect = [mock_check_result, mock_req_result]

        executor = CommandExecutor()
        result = executor.execute("user1", "确认 REQ-99999999-999", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"
        assert "不存在" in result.message


class TestExecuteParseError:
    """Test: FUNC/error — invalid command text returns error result."""

    def test_execute_parse_error(self):
        mock_db = MagicMock()
        executor = CommandExecutor()
        result = executor.execute("user1", "invalid text", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"
        assert "正确格式" in result.message


class TestExecuteRejectWithoutReason:
    """Test Q: FUNC/happy — reject without reason returns ok."""

    def test_execute_reject_no_reason(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260705-001"})

        mock_db.execute.side_effect = [mock_check_result, mock_req_result, MagicMock()]

        executor = CommandExecutor()
        result = executor.execute("user1", "驳回 REQ-20260705-001", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "ok"
        assert "已驳回 REQ-20260705-001" in result.message


class TestExecuteRejectPermissionDenied:
    """Test M: SEC/authz — reject also checks permission."""

    def test_execute_reject_permission_denied(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_db.execute.return_value = mock_check_result

        executor = CommandExecutor()
        result = executor.execute("user2", "驳回 REQ-20260705-001 意见", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"
        assert "无权限" in result.message


class TestExecutePermissionCheckForNonExistentRequirement:
    """Test N: SEC/authz — permission check returns False for non-existent req."""

    def test_permission_check_nonexistent_req(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = None

        mock_db.execute.return_value = mock_check_result

        executor = CommandExecutor()
        result = executor.execute("user1", "确认 REQ-99999999-999", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"
        assert "无权限" in result.message


class TestExecuteDbInsertFailure:
    """Test S: FUNC/error — DB insert failure returns error."""

    def test_execute_db_insert_failure(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260705-001"})

        mock_db.execute.side_effect = [
            mock_check_result,
            mock_req_result,
            OperationalError("db", {}, Exception("fail")),
        ]

        executor = CommandExecutor()
        result = executor.execute("user1", "确认 REQ-20260705-001", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"


class TestExecuteStatusHistoryInserted:
    """Test T: FUNC/state — confirm inserts StatusHistory row."""

    def test_confirm_inserts_status_history(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260705-001"})

        mock_insert_result = MagicMock()
        mock_db.execute.side_effect = [
            mock_check_result,
            mock_req_result,
            mock_insert_result,
        ]

        executor = CommandExecutor()
        result = executor.execute("user1", "确认 REQ-20260705-001", mock_db)

        assert result.status == "ok"
        assert mock_db.execute.call_count == 3
        mock_db.commit.assert_called_once()


class TestExecuteRejectInsertsStatusHistory:
    """Test T (reject): reject also inserts StatusHistory row."""

    def test_reject_inserts_status_history(self):
        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.first.return_value = _make_row({"submitter_id": "user1"})

        mock_req_result = MagicMock()
        mock_req_result.first.return_value = _make_row({"id": "REQ-20260705-001"})

        mock_insert_result = MagicMock()
        mock_db.execute.side_effect = [
            mock_check_result,
            mock_req_result,
            mock_insert_result,
        ]

        executor = CommandExecutor()
        result = executor.execute("user1", "驳回 REQ-20260705-001 修改意见", mock_db)

        assert result.status == "ok"
        assert mock_db.execute.call_count == 3
        mock_db.commit.assert_called_once()
