"""Requirement Detail Service — F022 需求详情页.

Provides RequirementDetailService.get_detail() returning a single requirement
with full info and status history timeline.
"""

from sqlalchemy.orm import Session, joinedload

from app.models import Requirements, StatusHistory, ReviewResults, DesignResults, ImplementationResults


class RequirementDetailService:
    """Service for fetching detailed requirement information."""

    @staticmethod
    def get_detail(db: Session, req_id: str) -> dict:
        """Return full detail of a single requirement by ID.

        Args:
            db: SQLAlchemy session.
            req_id: Requirement ID (e.g. REQ-20260709-0001).

        Returns:
            dict with requirement info + history timeline.

        Raises:
            ValueError: if req_id is empty.
            LookupError: if requirement not found.
        """
        if not req_id:
            raise ValueError("req_id is required")

        req = (
            db.query(Requirements)
            .options(
                joinedload(Requirements.review_results),
                joinedload(Requirements.design_results),
                joinedload(Requirements.implementation_results),
                joinedload(Requirements.status_history),
            )
            .filter(Requirements.id == req_id)
            .first()
        )

        if not req:
            raise LookupError(f"Requirement {req_id} not found")

        timeline = []
        for h in sorted(req.status_history, key=lambda x: x.triggered_at or x.id):
            timeline.append({
                "from_status": h.from_status,
                "to_status": h.to_status,
                "trigger_event": h.trigger_event,
                "trigger_user": h.trigger_user,
                "triggered_at": h.triggered_at.isoformat() if h.triggered_at else None,
            })

        return {
            "id": req.id,
            "original_text": req.original_text,
            "summary": req.summary,
            "submitter_id": req.submitter_id,
            "submitter_name": req.submitter_name,
            "tags": req.tags or [],
            "estimated_scope": req.estimated_scope,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "updated_at": req.updated_at.isoformat() if req.updated_at else None,
            "current_stage": req.current_stage,
            "current_status": req.current_status,
            "review_count": len(req.review_results),
            "design_count": len(req.design_results),
            "implementation_count": len(req.implementation_results),
            "timeline": timeline,
        }
