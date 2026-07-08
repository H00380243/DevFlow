"""Requirements Service — F021 需求列表与筛选搜索.

Provides RequirementsService.get_requirements() with filtered, paginated queries,
and create_requirement() for manual requirement intake.
"""

from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Requirements

VALID_PAGE_SIZES = {10, 20, 50}
REQUIRED_FIELDS = ["id", "summary", "submitter_id", "created_at", "current_stage", "current_status"]


class RequirementsService:
    """Handles requirement list queries with filtering, search, and pagination."""

    @staticmethod
    def get_requirements(db: Session, filters: dict) -> dict:
        """Return paginated, filtered list of requirements.

        Args:
            db: SQLAlchemy session.
            filters: dict with optional keys: page, page_size, stage, status, submitter, search.

        Returns:
            dict with items, total, page, page_size.

        Raises:
            ValueError: if page < 1 or page_size not in [10, 20, 50].
        """
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size not in VALID_PAGE_SIZES:
            raise ValueError("page_size must be 10, 20, or 50")

        query = db.query(Requirements)

        stage = filters.get("stage")
        if stage:
            query = query.filter(Requirements.current_stage == stage)

        status = filters.get("status")
        if status:
            query = query.filter(Requirements.current_status == status)

        submitter = filters.get("submitter")
        if submitter:
            query = query.filter(Requirements.submitter_id == submitter)

        search = filters.get("search")
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Requirements.id.like(like), Requirements.summary.like(like))
            )

        total = query.count()

        offset = (page - 1) * page_size
        items = query.order_by(Requirements.created_at.desc()).offset(offset).limit(page_size).all()

        return {
            "items": [
                {
                    "id": r.id,
                    "summary": r.summary,
                    "submitter_name": r.submitter_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "current_stage": r.current_stage,
                    "current_status": r.current_status,
                }
                for r in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def create_requirement(
        db: Session,
        original_text: str,
        summary: str,
        submitter_id: str,
        submitter_name: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Create a new requirement manually.

        Generates sequential ID (REQ-YYYYMMDD-NNN), sets initial stage/status.

        Args:
            db: SQLAlchemy session.
            original_text: Full requirement description.
            summary: Short summary.
            submitter_id: Submitter user ID.
            submitter_name: Optional display name.
            tags: Optional list of tags.

        Returns:
            dict of the created requirement.
        """
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"REQ-{today}-"

        last = (
            db.query(Requirements)
            .filter(Requirements.id.like(f"{prefix}%"))
            .order_by(Requirements.id.desc())
            .first()
        )
        if last:
            seq = int(last.id.split("-")[-1]) + 1
        else:
            seq = 1

        req_id = f"{prefix}{seq:03d}"

        now = datetime.now(timezone.utc)
        req = Requirements(
            id=req_id,
            original_text=original_text,
            summary=summary,
            submitter_id=submitter_id,
            submitter_name=submitter_name or submitter_id,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            current_stage="review",
            current_status="PENDING_REVIEW",
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        return {
            "id": req.id,
            "summary": req.summary,
            "submitter_name": req.submitter_name,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "current_stage": req.current_stage,
            "current_status": req.current_status,
        }
