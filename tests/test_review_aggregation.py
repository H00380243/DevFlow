"""Tests for AggregationService & ArbitrationHandler — F009 评审结论汇总与裁决."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, ArbitrationRequests, Requirements
from app.core.review_scoring import DimensionScores, Verdict
from app.core.state_machine import Event, Status


@pytest.fixture
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def state_machine():
    return MagicMock()


def _create_requirement(
    session: Session,
    req_id: str = "REQ-20260707-001",
    status: str = "PENDING_REVIEW",
    stage: str = "review",
) -> Requirements:
    req = Requirements(
        id=req_id,
        original_text="Test requirement",
        submitter_id="user1",
        current_stage=stage,
        current_status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(req)
    session.commit()
    return req


def _make_score(
    verdict: Verdict,
    role: str = "产品分析",
    bv: int = 4,
    tf: int = 4,
    roi: int = 4,
    sc: int = 4,
    comments: str | None = None,
) -> DimensionScores:
    return DimensionScores(
        agent_role=role,
        business_value=bv,
        technical_feasibility=tf,
        roi=roi,
        system_compatibility=sc,
        verdict=verdict,
        comments=comments,
    )


class TestAggregateThreeApprove:
    """Test A: FUNC/happy — 3 APPROVE → auto-pass."""

    def test_auto_pass(self, state_machine):
        from app.core.review_aggregation import (
            AggregationService,
            ArbitrationHandler,
            FinalDecision,
        )

        scores = [
            _make_score(Verdict.APPROVE, "产品分析"),
            _make_score(Verdict.APPROVE, "价值评估"),
            _make_score(Verdict.APPROVE, "技术可行性"),
        ]
        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision == FinalDecision.APPROVED
        assert state_machine.transition.call_count == 2
        state_machine.transition.assert_has_calls([
            call("REQ-20260707-001", Event.REVIEW_PASS),
            call("REQ-20260707-001", Event.REVIEW_PASS),
        ])
        arb_handler.request_arbitration.assert_not_called()


class TestAggregateTwoReject:
    """Test B: FUNC/happy — 2 REJECT + 1 APPROVE → arbitration."""

    def test_triggers_arbitration(self, state_machine):
        from app.core.review_aggregation import (
            AggregationService,
            ArbitrationHandler,
            FinalDecision,
        )

        scores = [
            _make_score(Verdict.REJECT, "产品分析"),
            _make_score(Verdict.REJECT, "价值评估"),
            _make_score(Verdict.APPROVE, "技术可行性"),
        ]
        state_machine.transition.return_value = Status.PENDING_ARBITRATION

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision == FinalDecision.NEEDS_ARBITRATION
        state_machine.transition.assert_called_once_with(
            "REQ-20260707-001", Event.REVIEW_REJECT
        )
        arb_handler.request_arbitration.assert_called_once()


class TestAggregateOneOneOne:
    """Test C: FUNC/happy — 1/1/1 (APPROVE/REJECT/NEUTRAL) → auto-pass."""

    def test_auto_pass(self, state_machine):
        from app.core.review_aggregation import (
            AggregationService,
            ArbitrationHandler,
            FinalDecision,
        )

        scores = [
            _make_score(Verdict.APPROVE, "产品分析"),
            _make_score(Verdict.REJECT, "价值评估"),
            _make_score(Verdict.NEUTRAL, "技术可行性"),
        ]
        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision == FinalDecision.APPROVED
        assert state_machine.transition.call_count == 2
        arb_handler.request_arbitration.assert_not_called()


class TestAggregateReviewResult:
    """Test D: FUNC/happy — risk_notes + suggested_priority computation."""

    def test_risk_notes_and_priority(self, state_machine):
        from app.core.review_aggregation import AggregationService, ArbitrationHandler

        scores = [
            _make_score(Verdict.APPROVE, "产品分析", bv=4, tf=4, roi=4, sc=4, comments="good"),
            _make_score(Verdict.APPROVE, "价值评估", bv=1, tf=5, roi=5, sc=5, comments=None),
            _make_score(Verdict.APPROVE, "技术可行性", bv=4, tf=4, roi=4, sc=4),
        ]
        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision.value == "APPROVED"
        assert len(result.scores) == 3
        assert "业务价值评分较低(1/5)" in result.risk_notes
        assert result.suggested_priority == 2


class TestAggregateTwoApproveOneNeutral:
    """Test E: FUNC/happy — 2 APPROVE + 1 NEUTRAL → auto-pass."""

    def test_auto_pass(self, state_machine):
        from app.core.review_aggregation import (
            AggregationService,
            ArbitrationHandler,
            FinalDecision,
        )

        scores = [
            _make_score(Verdict.APPROVE, "产品分析"),
            _make_score(Verdict.APPROVE, "价值评估"),
            _make_score(Verdict.NEUTRAL, "技术可行性"),
        ]
        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision == FinalDecision.APPROVED
        assert state_machine.transition.call_count == 2
        arb_handler.request_arbitration.assert_not_called()


class TestAggregateTwoRejectNeutral:
    """Test F: FUNC/happy — 2 REJECT + 1 NEUTRAL → arbitration."""

    def test_triggers_arbitration(self, state_machine):
        from app.core.review_aggregation import (
            AggregationService,
            ArbitrationHandler,
            FinalDecision,
        )

        scores = [
            _make_score(Verdict.REJECT, "产品分析"),
            _make_score(Verdict.REJECT, "价值评估"),
            _make_score(Verdict.NEUTRAL, "技术可行性"),
        ]
        state_machine.transition.return_value = Status.PENDING_ARBITRATION

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision == FinalDecision.NEEDS_ARBITRATION
        state_machine.transition.assert_called_once_with(
            "REQ-20260707-001", Event.REVIEW_REJECT
        )
        arb_handler.request_arbitration.assert_called_once()


class TestArbitrationRequest:
    """Test G: FUNC/happy — ArbitrationRequests DB row created."""

    def test_creates_db_row(self, db_session, state_machine):
        from app.core.review_aggregation import ArbitrationHandler

        _create_requirement(db_session)
        scores = [
            _make_score(Verdict.REJECT, "产品分析", bv=2),
            _make_score(Verdict.REJECT, "价值评估", bv=3),
        ]
        handler = ArbitrationHandler(db_session, state_machine)
        row = handler.request_arbitration("REQ-20260707-001", scores)

        assert row.id is not None
        assert row.requirement_id == "REQ-20260707-001"
        assert row.timeout_count == 0
        assert row.requested_at is not None
        assert row.responded_at is None
        assert "产品分析" in row.review_summary
        assert "反对" in row.review_summary
        assert "业务价值2分" in row.review_summary
        assert "价值评估" in row.review_summary


class TestArbitrationHandleResponseApproved:
    """Test H: FUNC/happy — handle_response approved → IN_DESIGN."""

    def test_approved_transitions(self, db_session, state_machine):
        from app.core.review_aggregation import ArbitrationHandler

        _create_requirement(db_session)
        scores = [_make_score(Verdict.REJECT, "产品分析")]
        handler = ArbitrationHandler(db_session, state_machine)
        handler.request_arbitration("REQ-20260707-001", scores)

        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]

        result = handler.handle_response(
            "REQ-20260707-001", approved=True, reason="ok", admin_id="admin1"
        )

        assert result == Status.IN_DESIGN
        state_machine.transition.assert_has_calls([
            call("REQ-20260707-001", Event.ARBITRATION_APPROVE),
            call("REQ-20260707-001", Event.REVIEW_PASS),
        ])

        arb = (
            db_session.query(ArbitrationRequests)
            .filter(ArbitrationRequests.requirement_id == "REQ-20260707-001")
            .first()
        )
        assert arb.responded_at is not None
        assert arb.admin_id == "admin1"
        assert arb.admin_response == "ok"


class TestArbitrationHandleResponseRejected:
    """Test I: FUNC/happy — handle_response rejected → REJECTED."""

    def test_rejected_transition(self, db_session, state_machine):
        from app.core.review_aggregation import ArbitrationHandler

        _create_requirement(db_session)
        scores = [_make_score(Verdict.REJECT, "产品分析")]
        handler = ArbitrationHandler(db_session, state_machine)
        handler.request_arbitration("REQ-20260707-001", scores)

        state_machine.transition.return_value = Status.REJECTED

        result = handler.handle_response(
            "REQ-20260707-001", approved=False, reason="no", admin_id="admin1"
        )

        assert result == Status.REJECTED
        state_machine.transition.assert_called_once_with(
            "REQ-20260707-001", Event.ARBITRATION_REJECT
        )

        arb = (
            db_session.query(ArbitrationRequests)
            .filter(ArbitrationRequests.requirement_id == "REQ-20260707-001")
            .first()
        )
        assert arb.responded_at is not None
        assert arb.admin_response == "no"


class TestAggregateThreeNeutral:
    """Test J: BNDRY/edge — 3 NEUTRAL → auto-pass (no majority against)."""

    def test_auto_pass(self, state_machine):
        from app.core.review_aggregation import (
            AggregationService,
            ArbitrationHandler,
            FinalDecision,
        )

        scores = [
            _make_score(Verdict.NEUTRAL, "产品分析"),
            _make_score(Verdict.NEUTRAL, "价值评估"),
            _make_score(Verdict.NEUTRAL, "技术可行性"),
        ]
        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]

        arb_handler = MagicMock(spec=ArbitrationHandler)
        service = AggregationService(state_machine, arb_handler)
        result = service.aggregate("REQ-20260707-001", scores)

        assert result.final_decision == FinalDecision.APPROVED
        assert state_machine.transition.call_count == 2
        arb_handler.request_arbitration.assert_not_called()


class TestComputeRiskNotesAllGood:
    """Test K: BNDRY/edge — all scores ≥ 3 → risk_notes empty."""

    def test_risk_notes_empty(self, state_machine):
        from app.core.review_aggregation import AggregationService

        service = AggregationService(state_machine, MagicMock())
        scores = [
            _make_score(Verdict.APPROVE, "产品分析", bv=3, tf=3, roi=3, sc=3),
            _make_score(Verdict.APPROVE, "价值评估", bv=4, tf=4, roi=4, sc=4),
        ]
        notes = service._compute_risk_notes(scores)
        assert notes == ""


class TestComputeRiskNotesLowScores:
    """Test L: BNDRY/edge — some scores ≤ 2 → risk_notes with details."""

    def test_risk_notes_contains_low_scores(self, state_machine):
        from app.core.review_aggregation import AggregationService

        service = AggregationService(state_machine, MagicMock())
        scores = [
            _make_score(
                Verdict.REJECT, "产品分析", bv=2, tf=5, roi=3, sc=5, comments="耗时较长"
            ),
        ]
        notes = service._compute_risk_notes(scores)
        assert "业务价值评分较低(2/5)" in notes
        assert "耗时较长" in notes


class TestComputeSuggestedPriorityHigh:
    """Test M: BNDRY/edge — avg(business_value) ≥ 4 → priority 1."""

    def test_priority_high(self, state_machine):
        from app.core.review_aggregation import AggregationService

        service = AggregationService(state_machine, MagicMock())
        scores = [
            _make_score(Verdict.APPROVE, "产品分析", bv=4),
            _make_score(Verdict.APPROVE, "价值评估", bv=5),
        ]
        priority = service._compute_suggested_priority(scores)
        assert priority == 1


class TestComputeSuggestedPriorityMedium:
    """Test N: BNDRY/edge — avg(business_value) ≥ 3 → priority 2."""

    def test_priority_medium(self, state_machine):
        from app.core.review_aggregation import AggregationService

        service = AggregationService(state_machine, MagicMock())
        scores = [
            _make_score(Verdict.APPROVE, "产品分析", bv=3),
            _make_score(Verdict.APPROVE, "价值评估", bv=3),
        ]
        priority = service._compute_suggested_priority(scores)
        assert priority == 2


class TestComputeSuggestedPriorityLow:
    """Test O: BNDRY/edge — avg(business_value) < 3 → priority 3."""

    def test_priority_low(self, state_machine):
        from app.core.review_aggregation import AggregationService

        service = AggregationService(state_machine, MagicMock())
        scores = [
            _make_score(Verdict.APPROVE, "产品分析", bv=2),
            _make_score(Verdict.APPROVE, "价值评估", bv=2),
        ]
        priority = service._compute_suggested_priority(scores)
        assert priority == 3


class TestAggregateEmptyScores:
    """Test P: FUNC/error — empty scores raises ValueError."""

    def test_raises_value_error(self, state_machine):
        from app.core.review_aggregation import AggregationService

        service = AggregationService(state_machine, MagicMock())
        with pytest.raises(ValueError, match="scores must not be empty"):
            service.aggregate("REQ-20260707-001", [])


class TestArbitrationHandleResponseNoActive:
    """Test Q: FUNC/error — handle_response with no active request."""

    def test_raises_not_found(self, db_session, state_machine):
        from app.core.review_aggregation import (
            ArbitrationHandler,
            ArbitrationNotFoundError,
        )

        _create_requirement(db_session)
        handler = ArbitrationHandler(db_session, state_machine)

        with pytest.raises(ArbitrationNotFoundError) as excinfo:
            handler.handle_response(
                "REQ-20260707-001",
                approved=True,
                reason="ok",
                admin_id="admin1",
            )
        assert "REQ-20260707-001" in str(excinfo.value)


class TestArbitrationHandleResponseAlreadyResponded:
    """Test R: FUNC/error — handle_response on already-responded request."""

    def test_raises_already_responded(self, db_session, state_machine):
        from app.core.review_aggregation import (
            ArbitrationAlreadyRespondedError,
            ArbitrationHandler,
        )

        _create_requirement(db_session)
        scores = [_make_score(Verdict.REJECT, "产品分析")]
        handler = ArbitrationHandler(db_session, state_machine)
        handler.request_arbitration("REQ-20260707-001", scores)

        state_machine.transition.side_effect = [
            Status.REVIEW_APPROVED,
            Status.IN_DESIGN,
        ]
        handler.handle_response(
            "REQ-20260707-001",
            approved=True,
            reason="ok",
            admin_id="admin1",
        )

        with pytest.raises(ArbitrationAlreadyRespondedError) as excinfo:
            handler.handle_response(
                "REQ-20260707-001",
                approved=True,
                reason="again",
                admin_id="admin2",
            )
        assert "REQ-20260707-001" in str(excinfo.value)
