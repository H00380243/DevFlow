"""Tests for CommandParser — F005 状态变更指令系统."""

import pytest
from app.core.command_parser import (
    Command,
    CommandParseError,
    CommandParser,
    ConfirmCommand,
    RejectCommand,
)


class TestParseConfirmHappyPath:
    """Test A: FUNC/happy — valid confirm command."""

    def test_parse_confirm_returns_confirm_command(self):
        parser = CommandParser()
        result = parser.parse("确认 REQ-20260705-001")
        assert isinstance(result, ConfirmCommand)
        assert result.command_type == "confirm"
        assert result.requirement_id == "REQ-20260705-001"


class TestParseRejectHappyPath:
    """Test B: FUNC/happy — valid reject command with reason."""

    def test_parse_reject_with_reason(self):
        parser = CommandParser()
        result = parser.parse("驳回 REQ-20260705-001 逻辑不清")
        assert isinstance(result, RejectCommand)
        assert result.command_type == "reject"
        assert result.requirement_id == "REQ-20260705-001"
        assert result.reason == "逻辑不清"


class TestParseNullInput:
    """Test E: BNDRY/edge — null input raises error."""

    def test_parse_none_raises(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="指令不能为空"):
            parser.parse(None)


class TestParseEmptyInput:
    """Test F: BNDRY/edge — empty string raises error."""

    def test_parse_empty_string_raises(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="指令不能为空"):
            parser.parse("")


class TestParseWhitespaceStripping:
    """Test G: BNDRY/edge — leading/trailing whitespace stripped."""

    def test_parse_with_surrounding_whitespace(self):
        parser = CommandParser()
        result = parser.parse("  确认 REQ-20260705-001  ")
        assert isinstance(result, ConfirmCommand)
        assert result.requirement_id == "REQ-20260705-001"


class TestParseMissingSpaceAfterConfirm:
    """Test H: BNDRY/edge — no space after 确认 raises error."""

    def test_parse_no_space_after_confirm(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式"):
            parser.parse("确认REQ-20260705-001")


class TestParseTrailingSpaceOnlyAfterConfirm:
    """Test I: BNDRY/edge — trailing space only after 确认 raises error."""

    def test_parse_trailing_space_after_confirm(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式"):
            parser.parse("确认 ")


class TestParseRejectWithoutReason:
    """Test J: BNDRY/edge — reject without reason returns empty reason."""

    def test_parse_reject_no_reason(self):
        parser = CommandParser()
        result = parser.parse("驳回 REQ-20260705-001")
        assert isinstance(result, RejectCommand)
        assert result.requirement_id == "REQ-20260705-001"
        assert result.reason == ""


class TestParseZeroDateReqId:
    """Test K: BNDRY/edge — zero-date REQ ID is valid."""

    def test_parse_zero_date(self):
        parser = CommandParser()
        result = parser.parse("确认 REQ-00000000-001")
        assert isinstance(result, ConfirmCommand)
        assert result.requirement_id == "REQ-00000000-001"


class TestParseFourDigitSeq:
    """Test L: BNDRY/edge — 4-digit sequence REQ ID is valid."""

    def test_parse_four_digit_seq(self):
        parser = CommandParser()
        result = parser.parse("确认 REQ-20260705-0001")
        assert isinstance(result, ConfirmCommand)
        assert result.requirement_id == "REQ-20260705-0001"


class TestParseInvalidReqId:
    """Test O: FUNC/error — malformed REQ ID raises error."""

    def test_parse_invalid_req_id_confirm(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式"):
            parser.parse("确认 REQ-invalid")

    def test_parse_invalid_req_id_reject(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式"):
            parser.parse("驳回 REQ-invalid")


class TestParseInvalidPrefix:
    """Test: FUNC/error — invalid command prefix raises error."""

    def test_parse_invalid_prefix(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="正确格式"):
            parser.parse("确认一下 REQ-20260705-001")


class TestParseWhitespaceOnlyInput:
    """Test: BNDRY/edge — whitespace-only input raises error."""

    def test_parse_whitespace_only(self):
        parser = CommandParser()
        with pytest.raises(CommandParseError, match="指令不能为空"):
            parser.parse("   ")


class TestParseCommandBaseClass:
    """Test: Command base class attributes."""

    def test_confirm_command_type(self):
        cmd = ConfirmCommand(requirement_id="REQ-20260705-001")
        assert cmd.command_type == "confirm"
        assert cmd.requirement_id == "REQ-20260705-001"

    def test_reject_command_type(self):
        cmd = RejectCommand(requirement_id="REQ-20260705-001", reason="too complex")
        assert cmd.command_type == "reject"
        assert cmd.requirement_id == "REQ-20260705-001"
        assert cmd.reason == "too complex"
