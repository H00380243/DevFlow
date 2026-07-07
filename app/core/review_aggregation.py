"""Review Aggregation & Arbitration — F009 评审结论汇总与裁决.

Consumes F008's list[DimensionScores], applies the 裁决规则 (≥2 APPROVE →
auto-pass, ≥2 REJECT → arbitration), drives F007's StateMachine transitions,
and manages the arbitration lifecycle.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.review_scoring import DimensionScores, Verdict
from app.core.state_machine import Event, StateMachine, Status
from app.models import ArbitrationRequests


class FinalDecision(str, Enum):
    APPROVED = "APPROVED"
    NEEDS_ARBITRATION = "NEEDS_ARBITRATION"


class ReviewResult(BaseModel):
    requirement_id: str
    scores: list[DimensionScores]
    final_decision: FinalDecision
    risk_notes: str = ""
    suggested_priority: int = Field(default=3, ge=1, le=3)


class ArbitrationNotFoundError(Exception):
    def __init__(self, req_id: str):
        self.req_id = req_id
        super().__init__(f"No active arbitration request found for: {req_id}")


class ArbitrationAlreadyRespondedError(Exception):
    def __init__(self, req_id: str):
        self.req_id = req_id
        super().__init__(f"Arbitration request for {req_id} already responded")


DIMENSION_MAP = {
    "business_value": "业务价值",
    "technical_feasibility": "技术可行性",
    "roi": "投入产出比",
    "system_compatibility": "系统兼容性",
}


def _decide(scores: list[DimensionScores]) -> tuple[FinalDecision, Event]:
    approve_count = sum(1 for s in scores if s.verdict == Verdict.APPROVE)
    reject_count = sum(1 for s in scores if s.verdict == Verdict.REJECT)

    if approve_count >= 2:
        return FinalDecision.APPROVED, Event.REVIEW_PASS
    elif reject_count >= 2:
        return FinalDecision.NEEDS_ARBITRATION, Event.REVIEW_REJECT
    else:
        return FinalDecision.APPROVED, Event.REVIEW_PASS


class AggregationService:
    def __init__(self, state_machine: StateMachine, arbitration_handler: "ArbitrationHandler"):
        self._sm = state_machine
        self._arbitration_handler = arbitration_handler

    def aggregate(self, req_id: str, scores: list[DimensionScores]) -> ReviewResult:
        if not scores:
            raise ValueError("scores must not be empty")

        decision, event = _decide(scores)

        new_status = self._sm.transition(req_id, event)

        if event == Event.REVIEW_PASS:
            if new_status == Status.REVIEW_APPROVED:
                new_status = self._sm.transition(req_id, Event.REVIEW_PASS)
        else:
            self._arbitration_handler.request_arbitration(req_id, scores)

        risk_notes = self._compute_risk_notes(scores)
        suggested_priority = self._compute_suggested_priority(scores)

        return ReviewResult(
            requirement_id=req_id,
            scores=scores,
            final_decision=decision,
            risk_notes=risk_notes,
            suggested_priority=suggested_priority,
        )

    def _compute_risk_notes(self, scores: list[DimensionScores]) -> str:
        risk_items: list[str] = []
        for score in scores:
            for dim_name, dim_label in DIMENSION_MAP.items():
                dim_value = getattr(score, dim_name)
                if dim_value <= 2:
                    note = f"- {score.agent_role}: {dim_label}评分较低({dim_value}/5)"
                    if score.comments:
                        note += f" - {score.comments}"
                    risk_items.append(note)
        return "\n".join(risk_items) if risk_items else ""

    def _compute_suggested_priority(self, scores: list[DimensionScores]) -> int:
        avg_bv = sum(s.business_value for s in scores) / len(scores)
        if avg_bv >= 4.0:
            return 1
        elif avg_bv >= 3.0:
            return 2
        else:
            return 3


class ArbitrationHandler:
    def __init__(self, session: Session, state_machine: StateMachine):
        self._session = session
        self._sm = state_machine

    def request_arbitration(
        self, req_id: str, scores: list[DimensionScores], trigger_user: str | None = None
    ) -> ArbitrationRequests:
        summary_lines: list[str] = []
        for score in scores:
            summary_lines.append(
                f"{score.agent_role}: {score.verdict.value} - 业务价值{score.business_value}分"
            )

        row = ArbitrationRequests(
            requirement_id=req_id,
            review_summary="\n".join(summary_lines),
            requested_at=datetime.now(timezone.utc),
            timeout_count=0,
        )
        self._session.add(row)
        self._session.commit()

        return row

    def handle_response(
        self, req_id: str, approved: bool, reason: str, admin_id: str
    ) -> Status:
        arb = (
            self._session.query(ArbitrationRequests)
            .filter(
                ArbitrationRequests.requirement_id == req_id,
                ArbitrationRequests.responded_at.is_(None),
            )
            .first()
        )

        if arb is None:
            existing = (
                self._session.query(ArbitrationRequests)
                .filter(ArbitrationRequests.requirement_id == req_id)
                .first()
            )
            if existing is not None:
                raise ArbitrationAlreadyRespondedError(req_id)
            raise ArbitrationNotFoundError(req_id)

        arb.admin_response = reason
        arb.admin_id = admin_id
        arb.responded_at = datetime.now(timezone.utc)
        self._session.commit()

        if approved:
            new_status = self._sm.transition(req_id, Event.ARBITRATION_APPROVE)
            if new_status == Status.REVIEW_APPROVED:
                new_status = self._sm.transition(req_id, Event.REVIEW_PASS)
        else:
            new_status = self._sm.transition(req_id, Event.ARBITRATION_REJECT)

        return new_status
