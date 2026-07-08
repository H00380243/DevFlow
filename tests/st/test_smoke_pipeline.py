"""Full-pipeline smoke test: input → process → store → retrieve → transition → output.

Exercises critical path through the system using ONLY real services (SQLite).
No mocks.

Critical path: Requirement create → query → state machine transition → action → verify.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, StatusHistory
from app.core.state_machine import StateMachine, Status
from app.core.requirement_action_service import RequirementActionService
from app.core.requirement_detail_service import RequirementDetailService
from app.core.requirements_service import RequirementsService
from app.core.dashboard_service import DashboardService


@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


class TestFullPipelineSmoke:
    """Full pipeline: create → query → transition → action → verify."""

    def test_create_query_transition_verify_smoke(self, session):
        """Complete data path: insert → list → detail → transition → action → verify."""

        # ---- Step 1: CREATE ----
        req = Requirements(
            id="REQ-20260709-0999",
            original_text="Smoke test requirement for full pipeline verification",
            summary="冲烟测试需求",
            submitter_id="smoke_user",
            current_stage="review",
            current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()

        # ---- Step 2: QUERY (list) ----
        svc = RequirementsService()
        result = svc.get_requirements(session, {"page": 1, "page_size": 10})
        assert result["total"] >= 1
        ids = [r["id"] for r in result["items"]]
        assert "REQ-20260709-0999" in ids

        # ---- Step 3: DETAIL ----
        detail = RequirementDetailService.get_detail(session, "REQ-20260709-0999")
        assert detail["id"] == "REQ-20260709-0999"
        assert detail["current_stage"] == "review"
        assert detail["current_status"] == "PENDING_REVIEW"

        # ---- Step 4: STATE MACHINE TRANSITION (confirm) ----
        sm = StateMachine(session)
        action_svc = RequirementActionService(session, sm)
        action_result = action_svc.execute_action(
            "REQ-20260709-0999", "confirm", "smoke_user"
        )
        assert action_result["status"] == "ok"

        verified = session.query(Requirements).filter_by(id="REQ-20260709-0999").first()
        assert verified.current_status == "REVIEW_APPROVED"

        # ---- Step 5: AUDIT TRAIL ----
        history_count = session.query(StatusHistory).filter_by(
            requirement_id="REQ-20260709-0999"
        ).count()
        assert history_count >= 1  # REVIEW_PASS

        # ---- Step 7: DASHBOARD METRICS ----
        metrics = DashboardService.get_metrics(session)
        assert metrics["total_requirements"] >= 1
        assert metrics["in_progress_count"] >= 0

    def test_reject_smoke(self, session):
        """Reject path: create → transition → reject → verify."""
        req = Requirements(
            id="REQ-20260709-0998",
            original_text="Reject smoke test",
            summary="驳回冲烟测试",
            submitter_id="smoke_user",
            current_stage="review",
            current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()

        sm = StateMachine(session)
        action_svc = RequirementActionService(session, sm)
        result = action_svc.execute_action(
            "REQ-20260709-0998", "reject", "smoke_user", "质量不达标"
        )
        assert result["status"] == "ok"

        req = session.query(Requirements).filter_by(id="REQ-20260709-0998").first()
        assert req.current_status == "PENDING_ARBITRATION"
