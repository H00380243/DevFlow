"""Requirement Parser — F004 需求结构化与 ID 生成."""

import hashlib
import re
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import IMMessage, StructuredRequirement


class RequirementParseError(Exception):
    """Raised when requirement parsing fails."""
    pass


class IdGenerationError(Exception):
    """Raised when requirement ID generation fails."""
    pass


class RequirementParser:
    """Parses IM messages into StructuredRequirement objects."""

    _CONSTRAINT_KEYWORDS = ["必须", "不能", "需要", "要求", "限制", "约束", "禁止", "至少", "最多"]
    _SENTENCE_SPLIT_RE = re.compile(r"[。！？.!?\n]")

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def parse(self, message: IMMessage) -> StructuredRequirement:
        """Parse an IM message into a StructuredRequirement.

        Args:
            message: The IM message to parse.

        Returns:
            StructuredRequirement with generated ID.

        Raises:
            RequirementParseError: When message content is None or empty.
        """
        if message.content is None or message.content.strip() == "":
            raise RequirementParseError("需求文本不能为空")

        intent = self._extract_intent(message.content)
        constraints = self._extract_constraints(message.content)
        req_id = self.generate_id()

        summary = intent if intent != "" else "待人工补充诉求"
        tags = self._extract_tags(message.content)

        return StructuredRequirement(
            id=req_id,
            original_text=message.content,
            summary=summary,
            submitter_id=message.sender_id,
            submitter_name=None,
            tags=tags,
            estimated_scope=None,
            created_at=datetime.now(timezone.utc),
        )

    def generate_id(self) -> str:
        """Generate a unique requirement ID in REQ-YYYYMMDD-NNN format.

        Returns:
            Unique requirement ID string.

        Raises:
            IdGenerationError: When DB query fails or sequence exhausted.
        """
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"REQ-{today}"

        try:
            result = self._db.execute(
                text(
                    "SELECT MAX(CAST(SUBSTR(id, :prefix_len) AS INTEGER)) "
                    "FROM requirements WHERE id LIKE :pattern"
                ),
                {"prefix_len": len(prefix) + 2, "pattern": f"{prefix}-%"},
            )
            max_seq = result.scalar()
        except Exception as exc:
            raise IdGenerationError("Failed to query sequence counter") from exc

        if max_seq is None:
            seq = 1
        elif max_seq >= 9999:
            raise IdGenerationError("Sequence exhausted for today")
        elif max_seq >= 999:
            seq = max_seq + 1
            return f"{prefix}-{seq:04d}"
        else:
            seq = max_seq + 1

        return f"{prefix}-{seq:03d}"

    def _extract_intent(self, content: str) -> str:
        """Extract the core intent from content (first sentence).

        Args:
            content: Non-empty content string.

        Returns:
            First sentence or truncated content; empty string if unparseable.
        """
        if not content or content.strip() == "":
            return ""

        parts = self._SENTENCE_SPLIT_RE.split(content)
        if parts and parts[0].strip() != "":
            result = parts[0].strip()
            return result[:200]

        stripped = content.strip()
        if stripped:
            return stripped[:200]

        return ""

    def _extract_constraints(self, content: str) -> list[str]:
        """Extract constraint phrases from content.

        Args:
            content: Non-empty content string.

        Returns:
            List of sentences containing constraint keywords.
        """
        if not content or content.strip() == "":
            return []

        parts = self._SENTENCE_SPLIT_RE.split(content)
        constraints = []
        for part in parts:
            sentence = part.strip()
            if sentence and any(kw in sentence for kw in self._CONSTRAINT_KEYWORDS):
                constraints.append(sentence)

        return constraints

    def _extract_tags(self, content: str) -> list[str]:
        """Extract tags from content (placeholder for future NLP logic).

        Args:
            content: Content string.

        Returns:
            List of tags (currently empty).
        """
        return []
