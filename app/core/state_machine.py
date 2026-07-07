"""State Machine — F007 状态机引擎.

Implements the requirement lifecycle state machine using SQLAlchemy for persistence.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Requirements, StatusHistory


class Status(str, Enum):
    """需求全生命周期状态枚举（14个）."""

    PENDING_REVIEW = "PENDING_REVIEW"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    PENDING_ARBITRATION = "PENDING_ARBITRATION"
    REJECTED = "REJECTED"
    IN_DESIGN = "IN_DESIGN"
    DESIGN_PENDING_CONFIRM = "DESIGN_PENDING_CONFIRM"
    DESIGN_CONFIRMED = "DESIGN_CONFIRMED"
    DESIGN_REJECTED = "DESIGN_REJECTED"
    IN_IMPLEMENTATION = "IN_IMPLEMENTATION"
    IMPL_PENDING_ACCEPTANCE = "IMPL_PENDING_ACCEPTANCE"
    IMPL_APPROVED = "IMPL_APPROVED"
    IMPL_REJECTED = "IMPL_REJECTED"
    DELIVERED = "DELIVERED"
    TERMINATED = "TERMINATED"


class Event(str, Enum):
    """状态机事件枚举（10个）."""

    SUBMIT = "SUBMIT"
    REVIEW_PASS = "REVIEW_PASS"
    REVIEW_REJECT = "REVIEW_REJECT"
    ARBITRATION_APPROVE = "ARBITRATION_APPROVE"
    ARBITRATION_REJECT = "ARBITRATION_REJECT"
    DESIGN_CONFIRM = "DESIGN_CONFIRM"
    DESIGN_REJECT = "DESIGN_REJECT"
    IMPL_CONFIRM = "IMPL_CONFIRM"
    IMPL_REJECT = "IMPL_REJECT"
    TIMEOUT = "TIMEOUT"
    DESIGN_COMPLETE = "DESIGN_COMPLETE"
    DESIGN_RETRY = "DESIGN_RETRY"
    IMPL_COMPLETE = "IMPL_COMPLETE"
    IMPL_SMOKE_FAIL = "IMPL_SMOKE_FAIL"
    IMPL_RETRY = "IMPL_RETRY"
    MAX_RETRY = "MAX_RETRY"


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current_status: Status, event: Event):
        self.current_status = current_status
        self.event = event
        super().__init__(
            f"Invalid transition: {current_status.value} + {event.value}"
        )


class RequirementNotFoundError(Exception):
    """Raised when a requirement is not found in the database."""

    def __init__(self, req_id: str):
        self.req_id = req_id
        super().__init__(f"Requirement not found: {req_id}")


class StateTransitionTable:
    """合法迁移表 — 定义状态流转规则."""

    def __init__(self):
        self._transitions: dict[tuple[Status, Event], Status] = {
            # PENDING_REVIEW transitions
            (Status.PENDING_REVIEW, Event.REVIEW_PASS): Status.REVIEW_APPROVED,
            (Status.PENDING_REVIEW, Event.REVIEW_REJECT): Status.PENDING_ARBITRATION,
            (Status.PENDING_REVIEW, Event.ARBITRATION_REJECT): Status.REJECTED,
            # PENDING_ARBITRATION transitions
            (Status.PENDING_ARBITRATION, Event.ARBITRATION_APPROVE): Status.REVIEW_APPROVED,
            (Status.PENDING_ARBITRATION, Event.ARBITRATION_REJECT): Status.REJECTED,
            (Status.PENDING_ARBITRATION, Event.TIMEOUT): Status.PENDING_ARBITRATION,
            # REVIEW_APPROVED auto-transition
            (Status.REVIEW_APPROVED, Event.REVIEW_PASS): Status.IN_DESIGN,
            # IN_DESIGN transitions
            (Status.IN_DESIGN, Event.DESIGN_COMPLETE): Status.DESIGN_PENDING_CONFIRM,
            # DESIGN_PENDING_CONFIRM transitions
            (Status.DESIGN_PENDING_CONFIRM, Event.DESIGN_CONFIRM): Status.DESIGN_CONFIRMED,
            (Status.DESIGN_PENDING_CONFIRM, Event.DESIGN_REJECT): Status.DESIGN_REJECTED,
            (Status.DESIGN_PENDING_CONFIRM, Event.TIMEOUT): Status.DESIGN_PENDING_CONFIRM,
            # DESIGN_REJECTED transitions
            (Status.DESIGN_REJECTED, Event.DESIGN_RETRY): Status.IN_DESIGN,
            (Status.DESIGN_REJECTED, Event.MAX_RETRY): Status.TERMINATED,
            # DESIGN_CONFIRMED auto-transition
            (Status.DESIGN_CONFIRMED, Event.DESIGN_CONFIRM): Status.IN_IMPLEMENTATION,
            # IN_IMPLEMENTATION transitions
            (Status.IN_IMPLEMENTATION, Event.IMPL_COMPLETE): Status.IMPL_PENDING_ACCEPTANCE,
            (Status.IN_IMPLEMENTATION, Event.IMPL_SMOKE_FAIL): Status.IN_IMPLEMENTATION,
            # IMPL_PENDING_ACCEPTANCE transitions
            (Status.IMPL_PENDING_ACCEPTANCE, Event.IMPL_CONFIRM): Status.IMPL_APPROVED,
            (Status.IMPL_PENDING_ACCEPTANCE, Event.IMPL_REJECT): Status.IMPL_REJECTED,
            # IMPL_REJECTED transitions
            (Status.IMPL_REJECTED, Event.IMPL_RETRY): Status.IN_IMPLEMENTATION,
            (Status.IMPL_REJECTED, Event.MAX_RETRY): Status.TERMINATED,
            # IMPL_APPROVED auto-transition
            (Status.IMPL_APPROVED, Event.IMPL_CONFIRM): Status.DELIVERED,
        }

    def is_valid(self, current_status: Status, event: Event) -> bool:
        """Check if a transition is valid."""
        return (current_status, event) in self._transitions

    def get_next(self, current_status: Status, event: Event) -> Status:
        """Get the next status for a valid transition."""
        return self._transitions[(current_status, event)]


# Add MAX_RETRY to Event if not already defined
if not hasattr(Event, "MAX_RETRY"):
    Event.MAX_RETRY = "MAX_RETRY"


class PersistenceManager:
    """SQLite 持久化管理器."""

    def __init__(self, session: Session):
        self._session = session

    def save_state(self, req_id: str, status: Status, from_status: Status | None = None,
                   trigger_event: str | None = None, trigger_user: str | None = None) -> None:
        """Save state to database (update requirement + insert history)."""
        now = datetime.now(timezone.utc)
        self._session.execute(
            text("UPDATE requirements SET current_status = :status, updated_at = :now WHERE id = :req_id"),
            {"status": status.value, "now": now, "req_id": req_id},
        )
        self._session.execute(
            text(
                "INSERT INTO status_history (requirement_id, from_status, to_status, "
                "trigger_event, trigger_user, triggered_at) "
                "VALUES (:req_id, :from_status, :to_status, :event, :user, :now)"
            ),
            {
                "req_id": req_id,
                "from_status": from_status.value if from_status else None,
                "to_status": status.value,
                "event": trigger_event,
                "user": trigger_user,
                "now": now,
            },
        )
        self._session.commit()

    def load_state(self, req_id: str) -> Status:
        """Load state from database."""
        result = self._session.execute(
            text("SELECT current_status FROM requirements WHERE id = :req_id"),
            {"req_id": req_id},
        )
        row = result.first()
        if row is None:
            raise RequirementNotFoundError(req_id)
        return Status(row.current_status)


class StateMachine:
    """需求全生命周期状态机."""

    MAX_RETRY_COUNT = 3

    def __init__(self, session: Session):
        self._session = session
        self._transition_table = StateTransitionTable()
        self._persistence = PersistenceManager(session)

    def _get_retry_count(self, req_id: str, event: Event) -> int:
        """Count the number of retries for a given event type."""
        event_name = event.value
        result = self._session.execute(
            text(
                "SELECT COUNT(*) FROM status_history "
                "WHERE requirement_id = :req_id AND trigger_event = :event"
            ),
            {"req_id": req_id, "event": event_name},
        )
        return result.scalar()

    def transition(self, req_id: str, event: Event, trigger_user: str | None = None) -> Status:
        """执行状态流转.

        Args:
            req_id: 需求ID
            event: 触发事件
            trigger_user: 触发用户（None表示系统自动流转）

        Returns:
            新状态

        Raises:
            RequirementNotFoundError: 需求不存在
            InvalidTransitionError: 非法状态迁移
        """
        result = self._session.execute(
            text("SELECT current_status FROM requirements WHERE id = :req_id"),
            {"req_id": req_id},
        )
        row = result.first()
        if row is None:
            raise RequirementNotFoundError(req_id)

        current_status = Status(row.current_status)

        # Check for max retry limit
        actual_event = event
        if event in (Event.DESIGN_RETRY, Event.IMPL_RETRY):
            retry_count = self._get_retry_count(req_id, event)
            if retry_count >= self.MAX_RETRY_COUNT:
                actual_event = Event.MAX_RETRY

        if not self._transition_table.is_valid(current_status, actual_event):
            self._session.execute(
                text(
                    "INSERT INTO status_history "
                    "(requirement_id, from_status, to_status, trigger_event, trigger_user, triggered_at) "
                    "VALUES (:req_id, NULL, NULL, :event, :user, :now)"
                ),
                {
                    "req_id": req_id,
                    "event": actual_event.value,
                    "user": trigger_user,
                    "now": datetime.now(timezone.utc),
                },
            )
            self._session.commit()
            raise InvalidTransitionError(current_status, actual_event)

        new_status = self._transition_table.get_next(current_status, actual_event)
        self._persistence.save_state(
            req_id, new_status, current_status, actual_event.value, trigger_user
        )
        return new_status

    def get_status(self, req_id: str) -> Status:
        """获取需求当前状态."""
        return self._persistence.load_state(req_id)

    def can_transition(self, req_id: str, event: Event) -> bool:
        """检查是否可以执行状态迁移."""
        current_status = self.get_status(req_id)
        return self._transition_table.is_valid(current_status, event)

    def save_state(self, req_id: str, status: Status) -> None:
        """保存状态（直接设置）."""
        self._persistence.save_state(req_id, status)

    def load_state(self, req_id: str) -> Status:
        """加载状态."""
        return self._persistence.load_state(req_id)
