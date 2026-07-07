"""Design Confirmation Handler — F014 设计确认门与迭代.

Orchestrates the design confirmation gate: IM push of design artifacts,
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


class DesignConfirmationHandler:
    def __init__(
        self,
        session: Session,
        push_fn: Callable[[str, str], None],
        design_team_fn: Callable[[str, str], None],
    ):
        self._session = session
        self._push_fn = push_fn
        self._design_team_fn = design_team_fn
        self._sm = StateMachine(session)

    def start_confirmation_gate(
        self, req_id: str, document_url: str, submitter_id: str
    ) -> None:
        status = self._sm.get_status(req_id)
        if status != Status.DESIGN_PENDING_CONFIRM:
            return
        message = (
            f"设计已完成 [{req_id}]\n"
            f"设计文档: {document_url}\n"
            f"请回复「确认 {req_id}」通过 或 「驳回 {req_id} 修改意见」驳回"
        )
        self._push_with_retry(submitter_id, message)

    def handle_confirm(self, req_id: str, sender_id: str) -> None:
        self._sm.get_status(req_id)
        new_status = self._sm.transition(req_id, Event.DESIGN_CONFIRM, sender_id)
        if new_status == Status.DESIGN_CONFIRMED:
            new_status = self._sm.transition(req_id, Event.DESIGN_CONFIRM, sender_id)
        self._push_fn(sender_id, f"已确认 {req_id}")
        logger.info("Design confirmed: %s by %s -> %s", req_id, sender_id, new_status.value)

    def handle_reject(self, req_id: str, sender_id: str, reason: str | None) -> None:
        self._validate_reject_reason(reason, sender_id)
        new_status = self._sm.transition(req_id, Event.DESIGN_REJECT, sender_id)
        if new_status == Status.IN_DESIGN:
            self._design_team_fn(req_id, feedback=reason or "")
            self._push_fn(sender_id, f"已驳回 {req_id}，意见已记录，重新启动设计流程")
        elif new_status == Status.TERMINATED:
            self._push_fn("admin", f"设计驳回达3轮，需求已终止: {req_id}")
        elif new_status == Status.DESIGN_REJECTED:
            retry_status = self._sm.transition(req_id, Event.DESIGN_RETRY, None)
            if retry_status == Status.IN_DESIGN:
                self._design_team_fn(req_id, feedback=reason or "")
                self._push_fn(sender_id, f"已驳回 {req_id}，意见已记录，重新启动设计流程")
            elif retry_status == Status.TERMINATED:
                self._push_fn("admin", f"设计驳回达3轮，需求已终止: {req_id}")
        logger.info("Design rejected: %s by %s -> %s", req_id, sender_id, new_status.value)

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
        handler: DesignConfirmationHandler | None = None,
    ):
        self._session = session
        self._push_fn = push_fn
        self._sm = StateMachine(session)
        self._handler = handler or DesignConfirmationHandler(
            session=session, push_fn=push_fn, design_team_fn=lambda r, **kw: None
        )

    def check_timeouts(self, now: datetime | None = None) -> list[TimeoutResult]:
        if now is None:
            now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=TIMEOUT_HOURS)
        try:
            rows = self._session.execute(
                text(
                    "SELECT id, submitter_id FROM requirements "
                    "WHERE current_status = 'DESIGN_PENDING_CONFIRM' AND updated_at <= :cutoff"
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
                    f"提醒: 设计确认({req_id})已超时4小时，请回复确认/驳回",
                )
                try:
                    self._sm.transition(req_id, Event.TIMEOUT, trigger_user=None)
                except Exception:
                    pass
                results.append(TimeoutResult(req_id, timeout_count + 1, escalated=False))
            else:
                self._push_fn(
                    "admin",
                    f"升级: 设计确认({req_id})超时已达3次，请管理员介入",
                )
                results.append(TimeoutResult(req_id, timeout_count, escalated=True))

        return results
