"""Arbitration Notification & Timeout Monitoring — F010 人工仲裁处理.

Provides ArbitrationNotifier (IM push with retry) and ArbitrationTimeoutMonitor
(4-hour timeout detection with escalation).
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from time import sleep
from typing import Callable

from sqlalchemy.orm import Session

from app.models import ArbitrationRequests


MAX_RETRIES = 3
TIMEOUT_HOURS = 4
ESCALATION_THRESHOLD = 3


class NotificationFailedError(Exception):
    """Raised when IM notification fails after all retries."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class TimeoutResult:
    req_id: str
    timeout_count: int
    escalated: bool
    reminded_at: datetime


class ArbitrationNotifier:
    """Pushes arbitration notification to admin via IM with retry logic."""

    def __init__(self, push_fn: Callable[[str, str], None] | None = None):
        self._push = push_fn or self._default_push

    def notify_admin(self, req_id: str, summary: str) -> None:
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._push(req_id, summary)
                return
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    sleep(2 ** attempt)
        raise NotificationFailedError(
            f"仲裁推送失败({MAX_RETRIES}次): {last_error}"
        )

    def _default_push(self, channel: str, message: str) -> None:
        raise NotImplementedError("IM push not configured")


class ArbitrationTimeoutMonitor:
    """Checks for overdue arbitration requests and sends reminders or escalation."""

    def __init__(self, session: Session, notifier: ArbitrationNotifier):
        self._session = session
        self._notifier = notifier

    def check_timeouts(self) -> list[TimeoutResult]:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=TIMEOUT_HOURS)
            overdue = (
                self._session.query(ArbitrationRequests)
                .filter(
                    ArbitrationRequests.responded_at.is_(None),
                    ArbitrationRequests.requested_at < cutoff,
                )
                .all()
            )
        except Exception:
            return []

        results: list[TimeoutResult] = []
        for req in overdue:
            escalated = False
            if req.timeout_count >= ESCALATION_THRESHOLD:
                self._notifier.notify_admin(
                    req.requirement_id, "升级: 仲裁超时需介入"
                )
                escalated = True
            else:
                self._notifier.notify_admin(
                    req.requirement_id, "提醒: 仲裁请求已超时"
                )
                req.timeout_count += 1
            self._session.commit()
            results.append(TimeoutResult(
                req_id=req.requirement_id,
                timeout_count=req.timeout_count,
                escalated=escalated,
                reminded_at=datetime.now(timezone.utc),
            ))
        return results
