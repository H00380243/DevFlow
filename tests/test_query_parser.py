"""Tests for F006 — 查询指令系统 (Progress/List command parsing and execution)."""

import pytest
from unittest.mock import MagicMock

from app.core.command_parser import (
    CommandParseError,
    CommandParser,
    ProgressCommand,
    ListCommand,
)
from app.core.command_executor import CommandExecutor, CommandResult


def _make_row(mapping: dict) -> MagicMock:
    """Create a mock row that supports row._mapping[key] access."""
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: mapping[key]
    mock_row._mapping = mapping
    return mock_row


# ============================================================
# CommandParser.parse — 进度 command
# ============================================================

class TestParseProgressHappyPath:
    """Test A: FUNC/happy — valid progress command."""

    def test_parse_progress_returns_progress_command(self):
        parser = CommandParser()
        result = parser.parse("进度 REQ-20260705-001")
        assert isinstance(result, ProgressCommand)
        assert result.requirement_id == "REQ-20260705-001"


class TestParseListHappyPath:
    """Test B: FUNC/happy — valid list command."""

    def test_parse_list_returns_list_command(self):
        parser = CommandParser()
        result = parser.parse("我的列表")
        assert isinstance(result, ListCommand)


# ============================================================
# CommandExecutor.execute — full path
# ============================================================

class TestExecuteProgressHappyPath:
    """Test C: FUNC/happy — progress command via CommandExecutor with DB."""

    def test_execute_progress_ok(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        row = MagicMock()
        row.current_stage = "评审"
        row.current_status = "待确认"
        mock_result.first.return_value = row
        mock_db.execute.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("U001", "进度 REQ-20260705-001", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "ok"
        assert "阶段=评审" in result.message
        assert "状态=待确认" in result.message
        assert "REQ-20260705-001" in result.message


class TestExecuteListHappyPath:
    """Test D: FUNC/happy — list command via CommandExecutor with DB."""

    def test_execute_list_ok(self):
        mock_db = MagicMock()

        row1 = MagicMock()
        row1.id = "REQ-20260705-001"
        row1.current_stage = "评审"
        row1.current_status = "待确认"

        row2 = MagicMock()
        row2.id = "REQ-20260705-002"
        row2.current_stage = "设计中"
        row2.current_status = "进行中"

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row1, row2]
        mock_db.execute.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("U001", "我的列表", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "ok"
        assert "您的需求清单" in result.message
        assert "REQ-20260705-001" in result.message
        assert "REQ-20260705-002" in result.message


class TestExecuteProgressNotFound:
    """Test E: FUNC/error — progress command, requirement not found."""

    def test_execute_progress_not_found(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("U001", "进度 REQ-20260705-999", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "error"
        assert "REQ-20260705-999" in result.message
        assert "不存在" in result.message


# ============================================================
# CommandParser.parse — error cases
# ============================================================

class TestParseProgressMissingReqId:
    """Test F: FUNC/error — progress command without REQ ID."""

    def test_parse_progress_without_req_id(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式: 进度 REQ-YYYYMMDD-NNN"):
            parser.parse("进度 ")


class TestParseUnrecognizedPrefix:
    """Test G: FUNC/error — unrecognized command prefix."""

    def test_parse_unrecognized_prefix(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式"):
            parser.parse("查询 REQ-20260705-001")


# ============================================================
# Boundary: None / empty / whitespace
# ============================================================

class TestParseProgressNone:
    """Test H: BNDRY/edge — None input raises CommandParseError."""

    def test_parse_none_raises(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="指令不能为空"):
            parser.parse(None)


class TestParseProgressEmpty:
    """Test I: BNDRY/edge — empty string raises CommandParseError."""

    def test_parse_empty_string_raises(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="指令不能为空"):
            parser.parse("")


class TestParseProgressWhitespaceOnly:
    """Test J: BNDRY/edge — whitespace-only input raises CommandParseError."""

    def test_parse_whitespace_only_raises(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="指令不能为空"):
            parser.parse("   ")


# ============================================================
# Boundary: whitespace variations in 进度
# ============================================================

class TestParseProgressDoubleSpace:
    """Test K: BNDRY/edge — double space after 进度."""

    def test_parse_progress_double_space(self):
        parser = CommandParser()
        result = parser.parse("进度  REQ-20260705-001")
        assert isinstance(result, ProgressCommand)
        assert result.requirement_id == "REQ-20260705-001"


class TestParseProgressLeadingTrailingSpaces:
    """Test L: BNDRY/edge — leading/trailing spaces stripped."""

    def test_parse_progress_surrounding_whitespace(self):
        parser = CommandParser()
        result = parser.parse("  进度 REQ-20260705-001  ")
        assert isinstance(result, ProgressCommand)
        assert result.requirement_id == "REQ-20260705-001"


# ============================================================
# Boundary: "我的列表" exact match
# ============================================================

class TestParseListExtraText:
    """Test M: BNDRY/edge — "我的列表" with extra text raises error."""

    def test_parse_list_with_extra_text(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError):
            parser.parse("我的列表 请查看")


# ============================================================
# Boundary: list empty result
# ============================================================

class TestExecuteListEmpty:
    """Test N: BNDRY/edge — list command with no results returns ok."""

    def test_execute_list_empty(self):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("U001", "我的列表", mock_db)

        assert isinstance(result, CommandResult)
        assert result.status == "ok"
        assert "暂无需求记录" in result.message


# ============================================================
# Boundary: invalid REQ ID in 进度
# ============================================================

class TestParseProgressInvalidReqId:
    """Test O: BNDRY/edge — invalid REQ ID format in progress command."""

    def test_parse_progress_invalid_req_id(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式: 进度 REQ-YYYYMMDD-NNN"):
            parser.parse("进度 REQ-invalid")
