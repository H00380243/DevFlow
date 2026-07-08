"""Delivery Archive Handler — F019 交付档案与状态归档.

Generates delivery archives (JSON), uploads to MinIO with retry,
persists to DB, transitions state to DELIVERED, and notifies submitter via IM.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.state_machine import Event, StateMachine, InvalidTransitionError
from app.models import DeliveryArchives


MAX_RETRIES = 3


class DeliveryArchiveHandler:
    """Orchestrates delivery archive creation, upload, persistence, state transition, and IM notification.

    Args:
        session: SQLAlchemy session
        push_fn: IM notification function (recipient, message) -> None
        upload_fn: MinIO upload function (req_id, archive_json) -> None
    """

    def __init__(
        self,
        session: Session,
        push_fn: Callable[[str, str], None],
        upload_fn: Callable[[str, str], None],
    ):
        self._session = session
        self._push_fn = push_fn
        self._upload_fn = upload_fn

    def create_archive(
        self,
        req_id: str,
        review_ref: str | None = None,
        design_ref: str | None = None,
        implementation_ref: str | None = None,
        commit_id: str = "",
        summary: str | None = None,
    ) -> dict[str, Any] | None:
        """Create delivery archive, upload, persist, transition state, notify.

        Returns:
            dict with archive_id and delivered_at on success, None if upload fails after retries.
        Raises:
            ValueError: if req_id or commit_id is empty.
            InvalidTransitionError: if state machine transition fails.
            NotificationFailedError: if IM notification fails after retries.
        """
        if not req_id:
            raise ValueError("req_id cannot be empty")
        if not commit_id:
            raise ValueError("commit_id cannot be empty")

        archive = {
            "requirement_id": req_id,
            "review_ref": review_ref,
            "design_ref": design_ref,
            "implementation_ref": implementation_ref,
            "commit_id": commit_id,
            "summary": summary,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }

        # Step 1: Upload to MinIO with retry
        upload_ok = False
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                self._upload_fn(req_id, json.dumps(archive))
                upload_ok = True
                break
            except TypeError:
                raise
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        if not upload_ok:
            # FR-017a AC2: notify admin, Git code already committed
            try:
                admin_msg = self.format_archive_message(req_id, commit_id, summary)
                self._push_fn(req_id, admin_msg)
            except Exception:
                pass
            return None

        # Step 2: Persist to DB
        archive_row = DeliveryArchives(
            requirement_id=req_id,
            review_ref=review_ref,
            design_ref=design_ref,
            implementation_ref=implementation_ref,
            summary=summary,
            delivered_at=datetime.now(timezone.utc),
        )
        self._session.add(archive_row)
        self._session.flush()

        # Step 3: State transition IMPL_APPROVED → DELIVERED
        sm = StateMachine(self._session)
        sm.transition(req_id, Event.IMPL_CONFIRM)

        # Step 4: IM notify submitter with retry
        delivered_msg = self.format_archive_message(req_id, commit_id, summary)
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                self._push_fn(req_id, delivered_msg)
                return {"archive_id": archive_row.id, "delivered_at": archive_row.delivered_at}
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        from app.core.arbitration_notification import NotificationFailedError
        raise NotificationFailedError(f"交付通知推送失败({MAX_RETRIES}次): {last_error}")

    def format_archive_message(self, req_id: str, commit_id: str, summary: str | None = None) -> str:
        """Format delivery notification message in Chinese."""
        msg = f"交付完成 [{req_id}]\n提交: {commit_id}"
        if summary:
            msg += f"\n总结: {summary}"
        return msg
