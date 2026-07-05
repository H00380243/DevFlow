"""Idempotency Checker — F004 重复提交幂等识别."""

import hashlib
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


class IdempotencyCheckError(Exception):
    """Raised when idempotency check fails."""
    pass


class IdempotencyStoreError(Exception):
    """Raised when idempotency store insert fails."""
    pass


class IdempotencyChecker:
    """Checks and stores idempotency records for message deduplication."""

    _IDEMPOTENCY_WINDOW_MINUTES = 5

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def check(self, sender_hash: int, content: str) -> str | None:
        """Check if a message is a duplicate within the idempotency window.

        Args:
            sender_hash: Hash of the sender identifier.
            content: Message content text.

        Returns:
            Existing requirement_id if duplicate found, None otherwise.

        Raises:
            IdempotencyCheckError: When DB query fails.
        """
        content_hash = self._hash_content(content)

        try:
            result = self._db.execute(
                text(
                    "SELECT requirement_id FROM idempotency_store "
                    "WHERE sender_hash = :sender_hash "
                    "AND content_hash = :content_hash "
                    "AND created_at > datetime('now', :window)"
                ),
                {
                    "sender_hash": sender_hash,
                    "content_hash": content_hash,
                    "window": f"-{self._IDEMPOTENCY_WINDOW_MINUTES} minutes",
                },
            )
            row = result.scalar()
        except Exception as exc:
            raise IdempotencyCheckError("Failed to check idempotency") from exc

        return row

    def store(self, sender_hash: int, content: str, req_id: str) -> None:
        """Store an idempotency record for future deduplication.

        Args:
            sender_hash: Hash of the sender identifier.
            content: Message content text.
            req_id: Generated requirement ID.

        Raises:
            IdempotencyStoreError: When DB insert fails.
        """
        content_hash = self._hash_content(content)

        try:
            self._db.execute(
                text(
                    "INSERT INTO idempotency_store "
                    "(sender_hash, content_hash, requirement_id, created_at) "
                    "VALUES (:sender_hash, :content_hash, :req_id, datetime('now'))"
                ),
                {
                    "sender_hash": sender_hash,
                    "content_hash": content_hash,
                    "req_id": req_id,
                },
            )
            self._db.commit()
        except Exception as exc:
            raise IdempotencyStoreError("Failed to store idempotency record") from exc

    @staticmethod
    def _hash_content(content: str) -> str:
        """Compute SHA256 hash of content string.

        Args:
            content: String to hash.

        Returns:
            Hex-encoded SHA256 hash.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
