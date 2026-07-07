"""Command Executor — F005/F006 状态变更与查询指令系统 / F010 人工仲裁处理."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.command_parser import (
    Command,
    CommandParseError,
    CommandParser,
    ConfirmCommand,
    ListCommand,
    ProgressCommand,
    RejectCommand,
)
from app.core.permission_checker import PermissionChecker
from app.core.state_machine import RequirementNotFoundError, StateMachine, Status

if TYPE_CHECKING:
    from app.core.review_aggregation import ArbitrationHandler


class CommandResult(BaseModel):
    """Result from CommandExecutor.execute()."""
    status: str = Field(..., pattern="^(ok|error)$")
    message: str


class QueryExecutor:
    """Executes query commands (progress/list) against the database."""

    def execute_query(self, command: Command, sender_id: str, db: Session) -> CommandResult:
        """Execute a query command.

        Args:
            command: Parsed command (ProgressCommand or ListCommand).
            sender_id: The sender's user identifier.
            db: SQLAlchemy database session.

        Returns:
            CommandResult with query results.
        """
        try:
            if isinstance(command, ProgressCommand):
                return self._execute_progress(command, db)
            elif isinstance(command, ListCommand):
                return self._execute_list(command, sender_id, db)
            else:
                return CommandResult(status="error", message="不支持的查询类型")
        except Exception:
            return CommandResult(status="error", message="系统错误")

    def _execute_progress(self, command: ProgressCommand, db: Session) -> CommandResult:
        """Execute progress query."""
        result = db.execute(
            text("SELECT current_stage, current_status FROM requirements WHERE id = :req_id"),
            {"req_id": command.requirement_id},
        )
        row = result.first()
        if row is None:
            return CommandResult(
                status="error",
                message=f"需求 {command.requirement_id} 不存在",
            )
        message = f"{command.requirement_id}: 阶段={row.current_stage}, 状态={row.current_status}"
        return CommandResult(status="ok", message=message)

    def _execute_list(self, command: ListCommand, sender_id: str, db: Session) -> CommandResult:
        """Execute list query."""
        result = db.execute(
            text(
                "SELECT id, current_stage, current_status "
                "FROM requirements WHERE submitter_id = :sender_id "
                "ORDER BY created_at DESC"
            ),
            {"sender_id": sender_id},
        )
        rows = result.fetchall()
        if not rows:
            return CommandResult(status="ok", message="暂无需求记录")
        lines = ["您的需求清单："]
        for i, row in enumerate(rows, 1):
            lines.append(f"{i}. {row.id} ({row.current_stage}-{row.current_status})")
        return CommandResult(status="ok", message="\n".join(lines))


class CommandExecutor:
    """Orchestrates command parsing, permission checking, and execution."""

    def __init__(self, state_machine: StateMachine | None = None,
                 arbitration_handler: "ArbitrationHandler | None" = None):
        self._parser = CommandParser()
        self._permission_checker = PermissionChecker()
        self._query_executor = QueryExecutor()
        self._state_machine = state_machine
        self._arbitration_handler = arbitration_handler

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

        # Query commands don't need permission check — dispatch immediately
        if isinstance(command, (ProgressCommand, ListCommand)):
            return self._query_executor.execute_query(command, sender_id, db)

        # Permission check for mutation commands (confirm/reject)
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

            # F010: Check for arbitration response routing
            if self._state_machine is not None and self._arbitration_handler is not None:
                if isinstance(command, (ConfirmCommand, RejectCommand)):
                    try:
                        current_status = self._state_machine.get_status(
                            command.requirement_id
                        )
                        if current_status == Status.PENDING_ARBITRATION:
                            approved = isinstance(command, ConfirmCommand)
                            reason = getattr(command, 'reason', '')
                            self._arbitration_handler.handle_response(
                                req_id=command.requirement_id,
                                approved=approved,
                                reason=reason,
                                admin_id=sender_id,
                            )
                            return CommandResult(
                                status="ok",
                                message=f"仲裁处理成功: {command.requirement_id}",
                            )
                    except RequirementNotFoundError:
                        pass

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
