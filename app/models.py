"""SQLAlchemy 2.0 declarative models for DemandFlow (Feature F002).

Defines 8 tables (Requirements, ReviewResults, DesignResults, ImplementationResults,
DeliveryArchives, StatusHistory, ArbitrationRequests, IdempotencyStore), a shared
``Base`` declarative class, and an ``init_db(engine)`` bootstrap helper.

Design reference: docs/features/2026-07-05-F002-data-model.md §3 Interface Contract.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Engine,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Shared declarative base for all DemandFlow ORM models."""
    pass


# CHECK for requirement id format: REQ-YYYYMMDD-NNN (3-digit) or
# REQ-YYYYMMDD-NNNN (4-digit, FR-002 expansion). ID generation is F004's job;
# this CHECK is a data-integrity guardrail only.
#
# NOTE: The design doc §5 pseudocode + Clarification Addendum #3 specify a GLOB
# with dashes between date components ('REQ-YYYY-MM-DD-NNN'), but the ER diagram
# (§3.1), FR-002, and Test Inventory row X all use the canonical
# 'REQ-YYYYMMDD-NNN' format (no dashes in the date). The GLOB below matches the
# canonical format; the design doc's dashed GLOB is a documentation error — see
# the Issues section of the F002 return report.
_REQ_ID_CHECK = (
    "id GLOB 'REQ-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9]' "
    "OR id GLOB 'REQ-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'"
)

_VERDICT_CHECK = "verdict IN ('通过','反对','中立')"


class Requirements(Base):
    """Requirements table — demand intake records."""

    __tablename__ = "requirements"
    __table_args__ = (
        CheckConstraint(_REQ_ID_CHECK, name="ck_requirements_id_format"),
        Index("ix_requirements_submitter_id", "submitter_id"),
        Index("ix_requirements_stage_status", "current_stage", "current_status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitter_id: Mapped[str] = mapped_column(Text, nullable=False)
    submitter_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    estimated_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    current_stage: Mapped[str] = mapped_column(Text, nullable=False)
    current_status: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    review_results: Mapped[list["ReviewResults"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    design_results: Mapped[list["DesignResults"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    implementation_results: Mapped[list["ImplementationResults"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    delivery_archives: Mapped[list["DeliveryArchives"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["StatusHistory"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    arbitration_requests: Mapped[list["ArbitrationRequests"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )


class ReviewResults(Base):
    """Review results table — multi-role agent scoring records."""

    __tablename__ = "review_results"
    __table_args__ = (
        CheckConstraint("business_value BETWEEN 1 AND 5", name="ck_review_business_value"),
        CheckConstraint("technical_feasibility BETWEEN 1 AND 5", name="ck_review_technical_feasibility"),
        CheckConstraint("roi BETWEEN 1 AND 5", name="ck_review_roi"),
        CheckConstraint("system_compatibility BETWEEN 1 AND 5", name="ck_review_system_compatibility"),
        CheckConstraint(_VERDICT_CHECK, name="ck_review_verdict"),
        Index("ix_review_results_requirement_id", "requirement_id"),
        Index("ix_review_results_agent_role", "agent_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(
        Text, ForeignKey("requirements.id"), nullable=False
    )
    agent_role: Mapped[str] = mapped_column(Text, nullable=False)
    business_value: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_feasibility: Mapped[int] = mapped_column(Integer, nullable=False)
    roi: Mapped[int] = mapped_column(Integer, nullable=False)
    system_compatibility: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(nullable=True)

    requirement: Mapped["Requirements"] = relationship(back_populates="review_results")


class DesignResults(Base):
    """Design results table — design artifacts produced by design agents."""

    __tablename__ = "design_results"
    __table_args__ = (
        Index("ix_design_results_requirement_id", "requirement_id"),
        Index("ix_design_results_version", "version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(
        Text, ForeignKey("requirements.id"), nullable=False
    )
    agent_role: Mapped[str] = mapped_column(Text, nullable=False)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    skeleton_dirs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    core_interfaces: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    requirement: Mapped["Requirements"] = relationship(back_populates="design_results")


class ImplementationResults(Base):
    """Implementation results table — code generation output records."""

    __tablename__ = "implementation_results"
    __table_args__ = (
        Index("ix_implementation_results_requirement_id", "requirement_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(
        Text, ForeignKey("requirements.id"), nullable=False
    )
    code_files: Mapped[list | None] = mapped_column(JSON, nullable=True)
    verification_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    branch_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    requirement: Mapped["Requirements"] = relationship(back_populates="implementation_results")


class DeliveryArchives(Base):
    """Delivery archives table — final delivery records."""

    __tablename__ = "delivery_archives"
    __table_args__ = (
        Index("ix_delivery_archives_requirement_id", "requirement_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(
        Text, ForeignKey("requirements.id"), nullable=False
    )
    review_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    design_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(nullable=True)

    requirement: Mapped["Requirements"] = relationship(back_populates="delivery_archives")


class StatusHistory(Base):
    """Status history table — state machine transition audit log."""

    __tablename__ = "status_history"
    __table_args__ = (
        Index("ix_status_history_requirement_id", "requirement_id"),
        Index("ix_status_history_triggered_at", "triggered_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(
        Text, ForeignKey("requirements.id"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_event: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_user: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_at: Mapped[datetime | None] = mapped_column(nullable=True)

    requirement: Mapped["Requirements"] = relationship(back_populates="status_history")


class ArbitrationRequests(Base):
    """Arbitration requests table — human-escalation request records."""

    __tablename__ = "arbitration_requests"
    __table_args__ = (
        CheckConstraint("timeout_count >= 0", name="ck_arbitration_timeout_count_nonneg"),
        Index("ix_arbitration_requests_requirement_id", "requirement_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(
        Text, ForeignKey("requirements.id"), nullable=False
    )
    admin_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime | None] = mapped_column(nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    timeout_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    requirement: Mapped["Requirements"] = relationship(back_populates="arbitration_requests")


class IdempotencyStore(Base):
    """Idempotency store table — 5-minute message deduplication.

    ``requirement_id`` is a SOFT reference (no FK constraint): idempotency check
    may happen before the requirement row is committed (FR-003). Strong FK would
    cause write failures (see design doc Clarification Addendum #1).
    """

    __tablename__ = "idempotency_store"
    __table_args__ = (
        Index("ix_idempotency_store_sender_content", "sender_hash", "content_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_hash: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)


def init_db(engine: Engine) -> None:
    """Create all 8 tables + indexes on the given engine (idempotent).

    Args:
        engine: A connected SQLAlchemy Engine targeting SQLite.

    Raises:
        ArgumentError: If engine is None.
        OperationalError: If the DB is not writable.

    Notes:
        Calls ``Base.metadata.create_all(engine)`` which is idempotent —
        already-existing tables are skipped.
    """
    if engine is None:
        from sqlalchemy.exc import ArgumentError
        raise ArgumentError("engine must not be None")
    Base.metadata.create_all(bind=engine)


# --- Pydantic models for IM Webhook (Feature F003) ---

from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Message type enum for IM message classification."""
    REQUIREMENT = "REQUIREMENT"
    COMMAND = "COMMAND"
    UNSUPPORTED = "UNSUPPORTED"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    VOICE = "VOICE"


class IMMessage(BaseModel):
    """IM message data class."""
    message_id: str = Field(..., min_length=1, max_length=100)
    sender_id: str = Field(..., min_length=1, max_length=100)
    content: str | None = Field(None, max_length=10000)
    timestamp: str
    message_type: MessageType = MessageType.TEXT


class MessageResult(BaseModel):
    """Result from MessageRouter.route()."""
    status: str = Field(..., pattern="^(ok|error)$")
    message: str


class WebhookPayload(BaseModel):
    """IM Webhook payload from external platform."""
    message_id: str = Field(..., min_length=1, max_length=100)
    sender_id: str = Field(..., min_length=1, max_length=100)
    content: str | None = Field(None, max_length=10000)
    timestamp: str
    message_type: str | None = None


class WebhookResponse(BaseModel):
    """Response from WebhookHandler.handle_webhook()."""
    status: str = Field(..., pattern="^(ok|error)$")
    message: str


class StructuredRequirement(BaseModel):
    """Structured requirement output from RequirementParser.parse()."""
    id: str = Field(..., min_length=1)
    original_text: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=0)
    submitter_id: str = Field(..., min_length=1)
    submitter_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    estimated_scope: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = [
    "Base",
    "Requirements",
    "ReviewResults",
    "DesignResults",
    "ImplementationResults",
    "DeliveryArchives",
    "StatusHistory",
    "ArbitrationRequests",
    "IdempotencyStore",
    "init_db",
    "IMMessage",
    "MessageType",
    "MessageResult",
    "WebhookPayload",
    "WebhookResponse",
    "StructuredRequirement",
]
