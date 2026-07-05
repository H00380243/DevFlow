"""Permission Checker — F005 状态变更指令系统."""

from sqlalchemy import text
from sqlalchemy.orm import Session


class PermissionCheckError(Exception):
    """Raised when permission check fails."""
    pass


class PermissionChecker:
    """Checks if a sender has permission to operate on a requirement."""

    def check_permission(self, sender_id: str, req_id: str, db: Session) -> bool:
        """Check if sender_id matches the requirement's submitter_id.

        Args:
            sender_id: The sender's user identifier.
            req_id: The requirement ID to check.
            db: SQLAlchemy database session.

        Returns:
            True if sender is the submitter, False otherwise.

        Raises:
            PermissionCheckError: When DB query fails.
        """
        try:
            result = db.execute(
                text("SELECT submitter_id FROM requirements WHERE id = :req_id"),
                {"req_id": req_id},
            )
            row = result.first()
        except Exception as exc:
            raise PermissionCheckError("Failed to check permission") from exc

        if row is None:
            return False

        return row._mapping["submitter_id"] == sender_id
