"""Rejection Notification — F011 评审驳回通知与归档."""

from time import sleep
from typing import Callable

from app.core.arbitration_notification import NotificationFailedError

MAX_RETRIES = 3


def format_rejection_message(req_id: str, reason: str, summary: str) -> str:
    reason_display = reason if reason else "未提供原因"
    summary_display = summary if summary else "无评审摘要"
    lines = [
        "需求评审驳回通知",
        "",
        f"需求编号：{req_id}",
        f"驳回原因：{reason_display}",
        "评审摘要：",
        summary_display,
        "",
        "如需重新提交，请发送新的需求描述。",
    ]
    return "\n".join(lines)


class RejectionNotifier:
    """Pushes rejection notification to submitter via IM with retry logic."""

    def __init__(self, push_fn: Callable[[str, str], None] | None = None):
        self._push = push_fn or self._default_push

    def notify_submitter(self, req_id: str, reason: str, summary: str) -> None:
        message = format_rejection_message(req_id, reason, summary)
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._push(req_id, message)
                return
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    sleep(2 ** attempt)
        raise NotificationFailedError(
            f"驳回推送失败({MAX_RETRIES}次): {last_error}"
        )

    def _default_push(self, channel: str, message: str) -> None:
        raise NotImplementedError("IM push not configured")
