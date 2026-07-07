"""Implementation Confirmation Handler — F017 实施确认门.

Orchestrates the implementation confirmation gate: IM push with verification result,
confirm/reject routing, 4-hour timeout monitoring, and reject iteration.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.state_machine import Event, RequirementNotFoundError, StateMachine, Status

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
TIMEOUT_HOURS = 4
ESCALATION_THRESHOLD = 3


class EmptyRejectReasonError(Exception):
    def __init__(self, message: str = "请提供修改意见"):
        self.message = message
        super().__init__(message)


@dataclass
class TimeoutResult:
    req_id: str
    timeout_count: int
    escalated: bool
    reminded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ImplementationConfirmationHandler:
    def __init__(
        self,
        session: Session,
        push_fn: Callable[[str, str], None],
        implementation_team_fn: Callable[[str, str], None],
    ):
        self._session = session
        self._push_fn = push_fn
        self._implementation_team_fn = implementation_team_fn
        self._sm = StateMachine(session)

    def start_confirmation_gate(
        self, req_id: str, verification_result: dict, submitter_id: str
    ) -> None:
        status = self._sm.get_status(req_id)
        if status != Status.IMPL_PENDING_ACCEPTANCE:
            return
        message = self._format_message(req_id, verification_result)
        self._push_with_retry(submitter_id, message)

    def handle_confirm(self, req_id: str, sender_id: str) -> Status:
        self._sm.get_status(req_id)
        new_status = self._sm.transition(req_id, Event.IMPL_CONFIRM, sender_id)
        if new_status == Status.IMPL_APPROVED:
            new_status = self._sm.transition(req_id, Event.IMPL_CONFIRM, sender_id)
        self._push_fn(sender_id, f"已确认 {req_id}")
        logger.info("Implementation confirmed: %s by %s -> %s", req_id, sender_id, new_status.value)
        return new_status

    def handle_reject(self, req_id: str, sender_id: str, reason: str | None) -> Status:
        self._validate_reject_reason(reason, sender_id)
        self._sm.transition(req_id, Event.IMPL_REJECT, sender_id)
        retry_status = self._sm.transition(req_id, Event.IMPL_RETRY, None)
        if retry_status == Status.IN_IMPLEMENTATION:
            self._implementation_team_fn(req_id, feedback=reason or "")
            self._push_fn(sender_id, f"已驳回 {req_id}，意见已记录，重新启动实施流程")
        elif retry_status == Status.TERMINATED:
            self._push_fn("admin", f"实施驳回达3轮，需求已终止: {req_id}")
        logger.info("Implementation rejected: %s by %s -> %s", req_id, sender_id, retry_status.value)
        return retry_status

    def _format_message(self, req_id: str, verification_result: dict) -> str:
        syntax_ok = verification_result.get("syntax_ok", False)
        imports_ok = verification_result.get("imports_ok", False)
        startup_ok = verification_result.get("startup_ok", False)
        all_pass = syntax_ok and imports_ok and startup_ok
        status_text = "冲烟验证通过" if all_pass else "冲烟验证部分失败"
        return (
            f"实施已完成 [{req_id}]\n"
            f"冲烟验证: {status_text}\n"
            f"   语法检查: {'✅' if syntax_ok else '❌'}\n"
            f"   导入检查: {'✅' if imports_ok else '❌'}\n"
            f"   启动检查: {'✅' if startup_ok else '❌'}\n"
            f"请回复「确认 {req_id}」通过 或 「驳回 {req_id} 修改意见」驳回"
        )

    def _push_with_retry(self, recipient: str, message: str) -> None:
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                self._push_fn(recipient, message)
                return
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
        from app.core.arbitration_notification import NotificationFailedError
        raise NotificationFailedError(f"推送失败({MAX_RETRIES}次): {last_error}")

    def _validate_reject_reason(self, reason: str | None, recipient: str = "") -> None:
        if reason is None or reason.strip() == "":
            if recipient:
                self._push_fn(recipient, "请提供修改意见")
            raise EmptyRejectReasonError()

    def _count_timeout_events(self, req_id: str) -> int:
        result = self._session.execute(
            text(
                "SELECT COUNT(*) FROM status_history "
                "WHERE requirement_id = :req_id AND trigger_event = 'TIMEOUT'"
            ),
            {"req_id": req_id},
        )
        return result.scalar() or 0


class ConfirmationTimeoutMonitor:
    def __init__(
        self,
        session: Session,
        push_fn: Callable[[str, str], None],
        handler: ImplementationConfirmationHandler | None = None,
    ):
        self._session = session
        self._push_fn = push_fn
        self._sm = StateMachine(session)
        self._handler = handler or ImplementationConfirmationHandler(
            session=session, push_fn=push_fn,
            implementation_team_fn=lambda r, **kw: None,
        )

    def check_timeouts(self, now: datetime | None = None) -> list[TimeoutResult]:
        if now is None:
            now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=TIMEOUT_HOURS)
        try:
            rows = self._session.execute(
                text(
                    "SELECT id, submitter_id FROM requirements "
                    "WHERE current_status = 'IMPL_PENDING_ACCEPTANCE' AND updated_at <= :cutoff"
                ),
                {"cutoff": cutoff},
            ).fetchall()
        except Exception:
            return []

        results: list[TimeoutResult] = []
        for row in rows:
            req_id = row.id
            submitter_id = row.submitter_id
            timeout_count = self._handler._count_timeout_events(req_id) if self._handler else 0

            if timeout_count < ESCALATION_THRESHOLD:
                self._push_fn(
                    submitter_id,
                    f"提醒: 实施确认({req_id})已超时4小时，请回复确认/驳回",
                )
                try:
                    self._sm.transition(req_id, Event.TIMEOUT, trigger_user=None)
                except Exception:
                    pass
                results.append(TimeoutResult(req_id, timeout_count + 1, escalated=False))
            else:
                self._push_fn(
                    "admin",
                    f"升级: 实施确认({req_id})超时已达3次，请管理员介入",
                )
                results.append(TimeoutResult(req_id, timeout_count, escalated=True))

        return results
