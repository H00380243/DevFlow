"""E2E: Cross-feature user workflows spanning multiple features.

Personas:
- 需求提交人 (Submitter): submit → confirm/reject → track
- 管理员 (Admin): arbitration → monitor
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements
from app.core.state_machine import StateMachine, Event
from app.core.requirement_action_service import RequirementActionService
from app.core.requirement_detail_service import RequirementDetailService
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


class TestSubmitterWorkflow:
    """E2E: 需求提交人 complete workflow."""

    def test_submitter_confirm_reject_list(self, session):
        """Scenario: Submitter confirms → rejects another → verify states."""
        sm = StateMachine(session)
        action_svc = RequirementActionService(session, sm)

        for i in range(3):
            req = Requirements(
                id=f"REQ-20260709-0{i}00",
                original_text=f"需求{i}",
                summary=f"测试需求{i}",
                submitter_id="submitter001",
                current_stage="review",
                current_status="PENDING_REVIEW",
            )
            session.add(req)
        session.commit()

        r1 = action_svc.execute_action("REQ-20260709-0000", "confirm", "submitter001")
        assert r1["status"] == "ok"

        r2 = action_svc.execute_action("REQ-20260709-0100", "reject", "submitter001", "范围过大")
        assert r2["status"] == "ok"

        req0 = session.query(Requirements).filter_by(id="REQ-20260709-0000").first()
        assert req0.current_status == "REVIEW_APPROVED"

        req1 = session.query(Requirements).filter_by(id="REQ-20260709-0100").first()
        assert req1.current_status == "PENDING_ARBITRATION"

        count = session.query(Requirements).filter_by(submitter_id="submitter001").count()
        assert count == 3

    def test_submitter_track_progress(self, session):
        """Scenario: Submitter checks detail and dashboard."""
        req = Requirements(
            id="REQ-20260709-0500",
            original_text="进度查询",
            summary="查询进度",
            submitter_id="submitter001",
            current_stage="review",
            current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()

        detail = RequirementDetailService.get_detail(session, "REQ-20260709-0500")
        assert detail["id"] == "REQ-20260709-0500"
        assert detail["current_status"] == "PENDING_REVIEW"

        metrics = DashboardService.get_metrics(session)
        assert metrics["total_requirements"] >= 1


class TestAdminWorkflow:
    """E2E: 管理员 complete workflow."""

    def test_admin_arbitration_and_dashboard(self, session):
        """Scenario: Arbitration → admin approves → check dashboard."""
        req = Requirements(
            id="REQ-20260709-0777",
            original_text="争议需求",
            summary="管理员仲裁测试",
            submitter_id="submitter001",
            current_stage="review",
            current_status="PENDING_ARBITRATION",
        )
        session.add(req)
        session.commit()

        sm = StateMachine(session)
        sm.transition("REQ-20260709-0777", Event.ARBITRATION_APPROVE, "admin001")
        session.commit()

        detail = RequirementDetailService.get_detail(session, "REQ-20260709-0777")
        assert detail["current_status"] == "REVIEW_APPROVED"

        metrics = DashboardService.get_metrics(session)
        assert metrics["total_requirements"] >= 1

    def test_admin_reject_arbitration_terminates(self, session):
        """Scenario: Admin rejects arbitration → REJECTED."""
        req = Requirements(
            id="REQ-20260709-0888",
            original_text="被驳回仲裁",
            summary="管理员驳回仲裁测试",
            submitter_id="submitter001",
            current_stage="review",
            current_status="PENDING_ARBITRATION",
        )
        session.add(req)
        session.commit()

        sm = StateMachine(session)
        sm.transition("REQ-20260709-0888", Event.ARBITRATION_REJECT, "admin001")
        session.commit()

        req = session.query(Requirements).filter_by(id="REQ-20260709-0888").first()
        assert req.current_status == "REJECTED"
