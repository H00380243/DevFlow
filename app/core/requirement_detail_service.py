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

        review_details = []
        for r in req.review_results:
            review_details.append({
                "agent_role": r.agent_role,
                "business_value": r.business_value,
                "technical_feasibility": r.technical_feasibility,
                "roi": r.roi,
                "system_compatibility": r.system_compatibility,
                "verdict": r.verdict,
                "comments": r.comments,
                "scored_at": r.scored_at.isoformat() if r.scored_at else None,
            })

        design_details = []
        for d in req.design_results:
            design_details.append({
                "agent_role": d.agent_role,
                "document_url": d.document_url,
                "skeleton_dirs": d.skeleton_dirs or [],
                "core_interfaces": d.core_interfaces or [],
                "risk_warnings": d.risk_warnings or [],
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "version": d.version,
            })

        implementation_details = []
        for i in req.implementation_results:
            implementation_details.append({
                "code_files": i.code_files or [],
                "verification_result": i.verification_result,
                "branch_name": i.branch_name,
                "commit_id": i.commit_id,
                "commit_message": i.commit_message,
                "committed_at": i.committed_at.isoformat() if i.committed_at else None,
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
            "review_details": review_details,
            "design_details": design_details,
            "implementation_details": implementation_details,
            "timeline": timeline,
        }
