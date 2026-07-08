"""Requirement Action Service — F023 看板操作与 IM 同步.

Provides REST-friendly confirm/reject actions on requirements,
triggering state machine transitions with audit logging.
"""

from sqlalchemy.orm import Session

from app.core.state_machine import StateMachine, Event, Status, InvalidTransitionError, RequirementNotFoundError


class ActionValidationError(ValueError):
    """Raised when an action request fails validation."""


_CONFIRM_EVENTS = {
    Status.PENDING_REVIEW: Event.REVIEW_PASS,
    Status.DESIGN_PENDING_CONFIRM: Event.DESIGN_CONFIRM,
    Status.IMPL_PENDING_ACCEPTANCE: Event.IMPL_CONFIRM,
}

_REJECT_EVENTS = {
    Status.PENDING_REVIEW: Event.REVIEW_REJECT,
    Status.DESIGN_PENDING_CONFIRM: Event.DESIGN_REJECT,
    Status.IMPL_PENDING_ACCEPTANCE: Event.IMPL_REJECT,
    Status.PENDING_ARBITRATION: Event.ARBITRATION_REJECT,
}


class RequirementActionService:
    """Service for executing confirm/reject actions on requirements."""

    def __init__(self, db: Session, state_machine: StateMachine):
        self._db = db
        self._sm = state_machine

    def execute_action(
        self,
        req_id: str,
        action: str,
        user_id: str,
        reason: str = "",
    ) -> dict:
        """Execute a confirm/reject action.

        Args:
            req_id: Requirement ID.
            action: 'confirm' or 'reject'.
            user_id: Actor identifier.
            reason: Required if action is 'reject'.

        Returns:
            dict with 'status' ('ok'|'error') and 'message'.

        Raises:
            ActionValidationError: on invalid parameters.
        """
        if not req_id:
            raise ActionValidationError("req_id is required")
        if action not in ("confirm", "reject"):
            raise ActionValidationError("action must be 'confirm' or 'reject'")
        if not user_id:
            raise ActionValidationError("user_id is required")
        if action == "reject" and not reason:
            raise ActionValidationError("reason is required for reject actions")

        try:
            current = self._sm.get_status(req_id)
        except RequirementNotFoundError:
            return {"status": "error", "message": f"需求 {req_id} 不存在"}

        event_map = _CONFIRM_EVENTS if action == "confirm" else _REJECT_EVENTS
        event = event_map.get(current)
        if event is None:
            return {
                "status": "error",
                "message": f"当前状态 {current.value} 不支持{ '确认' if action == 'confirm' else '驳回' }操作",
            }

        try:
            self._sm.transition(req_id, event, user_id)
            self._db.commit()
            return {
                "status": "ok",
                "message": f"已完成{'确认' if action == 'confirm' else '驳回'}: {req_id}",
            }
        except InvalidTransitionError:
            self._db.rollback()
            return {"status": "error", "message": "状态流转不允许"}
