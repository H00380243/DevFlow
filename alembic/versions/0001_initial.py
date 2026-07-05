"""initial schema — 8 tables for F002

Revision ID: 0001
Revises:
Create Date: 2026-07-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all 8 tables + indexes per design doc §3 Interface Contract / §5 Algorithm.

    Order respects FK dependencies: parent (requirements) first, then 6 child
    tables with FK to requirements.id, then idempotency_store (soft FK, no constraint).
    """
    # --- requirements (parent) ---
    op.create_table(
        "requirements",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("submitter_id", sa.Text(), nullable=False),
        sa.Column("submitter_name", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("estimated_scope", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("current_stage", sa.Text(), nullable=False),
        sa.Column("current_status", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "id GLOB 'REQ-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9]' "
            "OR id GLOB 'REQ-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'",
            name="ck_requirements_id_format",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_requirements_submitter_id", "requirements", ["submitter_id"])
    op.create_index(
        "ix_requirements_stage_status", "requirements",
        ["current_stage", "current_status"],
    )

    # --- review_results ---
    op.create_table(
        "review_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("agent_role", sa.Text(), nullable=False),
        sa.Column("business_value", sa.Integer(), nullable=False),
        sa.Column("technical_feasibility", sa.Integer(), nullable=False),
        sa.Column("roi", sa.Integer(), nullable=False),
        sa.Column("system_compatibility", sa.Integer(), nullable=False),
        sa.Column("verdict", sa.Text(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("scored_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("business_value BETWEEN 1 AND 5", name="ck_review_business_value"),
        sa.CheckConstraint("technical_feasibility BETWEEN 1 AND 5", name="ck_review_technical_feasibility"),
        sa.CheckConstraint("roi BETWEEN 1 AND 5", name="ck_review_roi"),
        sa.CheckConstraint("system_compatibility BETWEEN 1 AND 5", name="ck_review_system_compatibility"),
        sa.CheckConstraint("verdict IN ('通过','反对','中立')", name="ck_review_verdict"),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_results_requirement_id", "review_results", ["requirement_id"])
    op.create_index("ix_review_results_agent_role", "review_results", ["agent_role"])

    # --- design_results ---
    op.create_table(
        "design_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("agent_role", sa.Text(), nullable=False),
        sa.Column("document_url", sa.Text(), nullable=True),
        sa.Column("skeleton_dirs", sa.JSON(), nullable=True),
        sa.Column("core_interfaces", sa.JSON(), nullable=True),
        sa.Column("risk_warnings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_design_results_requirement_id", "design_results", ["requirement_id"])
    op.create_index("ix_design_results_version", "design_results", ["version"])

    # --- implementation_results ---
    op.create_table(
        "implementation_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("code_files", sa.JSON(), nullable=True),
        sa.Column("verification_result", sa.JSON(), nullable=True),
        sa.Column("branch_name", sa.Text(), nullable=True),
        sa.Column("commit_id", sa.Text(), nullable=True),
        sa.Column("commit_message", sa.Text(), nullable=True),
        sa.Column("committed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_implementation_results_requirement_id",
        "implementation_results", ["requirement_id"],
    )

    # --- delivery_archives ---
    op.create_table(
        "delivery_archives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("review_ref", sa.Text(), nullable=True),
        sa.Column("design_ref", sa.Text(), nullable=True),
        sa.Column("implementation_ref", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_delivery_archives_requirement_id", "delivery_archives", ["requirement_id"],
    )

    # --- status_history ---
    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=True),
        sa.Column("trigger_event", sa.Text(), nullable=True),
        sa.Column("trigger_user", sa.Text(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_status_history_requirement_id", "status_history", ["requirement_id"])
    op.create_index("ix_status_history_triggered_at", "status_history", ["triggered_at"])

    # --- arbitration_requests ---
    op.create_table(
        "arbitration_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=False),
        sa.Column("admin_id", sa.Text(), nullable=True),
        sa.Column("review_summary", sa.Text(), nullable=True),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("timeout_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("timeout_count >= 0", name="ck_arbitration_timeout_count_nonneg"),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_arbitration_requests_requirement_id",
        "arbitration_requests", ["requirement_id"],
    )

    # --- idempotency_store (soft FK — no FK constraint, per design Addendum #1) ---
    op.create_table(
        "idempotency_store",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sender_hash", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("requirement_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_idempotency_store_sender_content",
        "idempotency_store", ["sender_hash", "content_hash"],
    )


def downgrade() -> None:
    """Drop all 8 tables in reverse FK-dependency order (children first)."""
    op.drop_table("idempotency_store")
    op.drop_table("arbitration_requests")
    op.drop_table("status_history")
    op.drop_table("delivery_archives")
    op.drop_table("implementation_results")
    op.drop_table("design_results")
    op.drop_table("review_results")
    op.drop_table("requirements")
