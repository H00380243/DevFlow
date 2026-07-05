"""Command Executor — F005 状态变更指令系统."""

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.command_parser import (
    Command,
    CommandParseError,
    CommandParser,
    ConfirmCommand,
)
from app.core.permission_checker import PermissionChecker


class CommandResult(BaseModel):
    """Result from CommandExecutor.execute()."""
    status: str = Field(..., pattern="^(ok|error)$")
    message: str


class CommandExecutor:
    """Orchestrates command parsing, permission checking, and execution."""

    def __init__(self):
        self._parser = CommandParser()
        self._permission_checker = PermissionChecker()

    def execute(self, sender_id: str, command_text: str, db: Session) -> CommandResult:
        """Execute a command from IM text.

        Args:
            sender_id: The sender's user identifier.
            command_text: Raw IM message text.
            db: SQLAlchemy database session.

        Returns:
            CommandResult with status and message.
        """
        try:
            command = self._parser.parse(command_text)
        except CommandParseError as e:
            return CommandResult(status="error", message=str(e))

        has_permission = self._permission_checker.check_permission(
            sender_id, command.requirement_id, db
        )
        if not has_permission:
            return CommandResult(status="error", message="无权限：仅提交人可操作")

        try:
            result = db.execute(
                text("SELECT id FROM requirements WHERE id = :req_id"),
                {"req_id": command.requirement_id},
            )
            if result.first() is None:
                return CommandResult(
                    status="error",
                    message=f"需求 {command.requirement_id} 不存在",
                )

            db.execute(
                text(
                    "INSERT INTO status_history "
                    "(requirement_id, trigger_event, trigger_user, triggered_at) "
                    "VALUES (:req_id, :event, :user, datetime('now'))"
                ),
                {
                    "req_id": command.requirement_id,
                    "event": command.command_type,
                    "user": sender_id,
                },
            )
            db.commit()
        except Exception:
            return CommandResult(status="error", message="系统错误")

        if isinstance(command, ConfirmCommand):
            return CommandResult(
                status="ok", message=f"已确认 {command.requirement_id}"
            )
        else:
            msg = f"已驳回 {command.requirement_id}"
            if command.reason:
                msg = msg + " " + command.reason
            return CommandResult(status="ok", message=msg)
