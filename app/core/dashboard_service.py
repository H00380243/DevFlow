"""Dashboard Service — F020 看板首页指标.

Provides DashboardService.get_metrics() computing total_requirements, review_pass_rate,
and in_progress_count from the Requirements model.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Requirements

APPROVED_STATES = [
    "REVIEW_APPROVED", "IN_DESIGN", "DESIGN_PENDING_CONFIRM",
    "DESIGN_CONFIRMED", "IN_IMPLEMENTATION", "IMPL_PENDING_ACCEPTANCE",
    "IMPL_APPROVED", "DELIVERED",
]

TERMINAL_STATES = ["DELIVERED", "REJECTED", "TERMINATED"]


class DashboardService:
    """Computes dashboard metrics from the requirements database."""

    @staticmethod
    def get_metrics(db: Session) -> dict:
        """Compute and return dashboard metrics.

        Returns:
            dict with total_requirements, review_pass_rate, in_progress_count, errors.
        """
        errors: list[str] = []

        try:
            total_count = db.query(func.count(Requirements.id)).scalar() or 0
        except Exception as e:
            raise

        try:
            approved_count = db.query(func.count(Requirements.id)).filter(
                Requirements.current_status.in_(APPROVED_STATES)
            ).scalar() or 0
        except Exception as e:
            errors.append(f"approved_count query failed: {e}")
            approved_count = 0

        try:
            in_progress_count = db.query(func.count(Requirements.id)).filter(
                ~Requirements.current_status.in_(TERMINAL_STATES)
            ).scalar() or 0
        except Exception as e:
            errors.append(f"in_progress_count query failed: {e}")
            in_progress_count = 0

        if total_count == 0:
            approval_rate = None
        else:
            approval_rate = round(approved_count / total_count * 100, 1)

        result = {
            "total_requirements": total_count,
            "review_pass_rate": approval_rate,
            "in_progress_count": in_progress_count,
        }
        if errors:
            result["errors"] = errors
        return result
