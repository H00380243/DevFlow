"""Command Parser — F005/F006 状态变更与查询指令系统."""

import re
from dataclasses import dataclass, field

# REQ ID pattern: REQ-YYYYMMDD-NNN (3-digit) or REQ-YYYYMMDD-NNNN (4-digit)
REQ_ID_PATTERN = re.compile(r"^REQ-\d{8}-\d{3,4}$")


class CommandParseError(Exception):
    """Raised when command parsing fails."""
    pass


@dataclass
class Command:
    """Base command dataclass."""
    requirement_id: str = ""
    command_type: str = field(init=False)


@dataclass
class ConfirmCommand(Command):
    """Confirm command — confirms a requirement."""
    command_type: str = field(init=False, default="confirm")

    def __post_init__(self):
        self.command_type = "confirm"


@dataclass
class RejectCommand(Command):
    """Reject command — rejects a requirement with optional reason."""
    command_type: str = field(init=False, default="reject")
    reason: str = ""

    def __post_init__(self):
        self.command_type = "reject"


@dataclass
class ProgressCommand(Command):
    """Progress command — queries requirement progress."""
    command_type: str = field(init=False, default="progress")

    def __post_init__(self):
        self.command_type = "progress"


@dataclass
class ListCommand(Command):
    """List command — queries submitter's requirement list."""
    command_type: str = field(init=False, default="list")

    def __post_init__(self):
        self.command_type = "list"


class CommandParser:
    """Parses IM command text into Command objects."""

    def parse(self, text: str | None) -> Command:
        """Parse command text into a Command object.

        Args:
            text: Raw IM message text (e.g., "确认 REQ-20260705-001").

        Returns:
            ConfirmCommand, RejectCommand, ProgressCommand, or ListCommand.

        Raises:
            CommandParseError: If text is empty, None, or format is invalid.
        """
        if text is None or text.strip() == "":
            raise CommandParseError("指令不能为空")

        text = text.strip()

        if text.startswith("进度"):
            return self._parse_progress(text)

        if text == "我的列表":
            return self._parse_list(text)

        if text.startswith("确认 "):
            return self._parse_confirm(text)

        if text.startswith("驳回 "):
            return self._parse_reject(text)

        raise CommandParseError("正确格式: 确认/驳回/进度 REQ-YYYYMMDD-NNN 或 我的列表")

    def _parse_confirm(self, text: str) -> ConfirmCommand:
        """Parse confirm command text.

        Args:
            text: Text starting with '确认 '.

        Returns:
            ConfirmCommand.

        Raises:
            CommandParseError: If REQ ID is missing or invalid.
        """
        parts = text.split(maxsplit=1)
        if len(parts) == 2 and REQ_ID_PATTERN.match(parts[1]):
            return ConfirmCommand(requirement_id=parts[1])
        raise CommandParseError("正确格式: 确认 REQ-YYYYMMDD-NNN")

    def _parse_reject(self, text: str) -> RejectCommand:
        """Parse reject command text.

        Args:
            text: Text starting with '驳回 '.

        Returns:
            RejectCommand.

        Raises:
            CommandParseError: If REQ ID is missing or invalid.
        """
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            sub_parts = parts[1].split(" ", maxsplit=1)
            if REQ_ID_PATTERN.match(sub_parts[0]):
                reason = sub_parts[1] if len(sub_parts) > 1 else ""
                return RejectCommand(requirement_id=sub_parts[0], reason=reason)
        raise CommandParseError("正确格式: 驳回 REQ-YYYYMMDD-NNN 修改意见XXX")

    def _parse_progress(self, text: str) -> ProgressCommand:
        """Parse progress command text.

        Args:
            text: Text starting with '进度'.

        Returns:
            ProgressCommand.

        Raises:
            CommandParseError: If REQ ID is missing or invalid.
        """
        after_keyword = text[len("进度"):]
        if not after_keyword or not after_keyword.strip():
            raise CommandParseError("正确格式: 进度 REQ-YYYYMMDD-NNN")
        parts = after_keyword.strip().split(maxsplit=1)
        if len(parts) == 1 and REQ_ID_PATTERN.match(parts[0]):
            return ProgressCommand(requirement_id=parts[0])
        raise CommandParseError("正确格式: 进度 REQ-YYYYMMDD-NNN")

    def _parse_list(self, text: str) -> ListCommand:
        """Parse list command text.

        Args:
            text: Exact match '我的列表'.

        Returns:
            ListCommand.
        """
        return ListCommand()
