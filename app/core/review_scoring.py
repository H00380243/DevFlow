"""Review Scoring — F008 评审团多角色打分.

Implements 3-role parallel review agent scoring with exponential backoff retry.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.state_machine import RequirementNotFoundError
from app.models import Requirements, ReviewResults, StructuredRequirement

logger = logging.getLogger(__name__)

T = TypeVar("T")

PROMPT_TEMPLATE = (
    "你是一个{role_name}评审专家。请对以下需求进行评审打分。\n\n"
    "需求ID: {req_id}\n"
    "需求描述: {original_text}\n"
    "需求摘要: {summary}\n\n"
    "请从以下4个维度按1-5分评分：\n"
    "1. 业务价值 (business_value)\n"
    "2. 技术可行性 (technical_feasibility)\n"
    "3. 投入产出比 (roi)\n"
    "4. 系统兼容性 (system_compatibility)\n\n"
    "并给出总体结论 (verdict: 通过/反对/中立)。\n"
    "请以JSON格式返回，例如：\n"
    '{{"business_value":4,"technical_feasibility":4,"roi":3,"system_compatibility":4,"verdict":"通过","comments":"..."}}'
)


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    on_exhausted: Callable[[Exception], None] | None = None,
) -> T | None:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except (LLMCallError, ScoreParseError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    if on_exhausted and last_error is not None:
        on_exhausted(last_error)
    return None


class Verdict(str, Enum):
    APPROVE = "通过"
    REJECT = "反对"
    NEUTRAL = "中立"


class DimensionScores(BaseModel):
    agent_role: str = Field(..., min_length=1)
    business_value: int = Field(..., ge=1, le=5)
    technical_feasibility: int = Field(..., ge=1, le=5)
    roi: int = Field(..., ge=1, le=5)
    system_compatibility: int = Field(..., ge=1, le=5)
    verdict: Verdict
    comments: str | None = None


class ReviewScores(BaseModel):
    requirement_id: str
    scores: list[DimensionScores]


class AllAgentsFailedError(Exception):
    def __init__(self, req_id: str):
        self.req_id = req_id
        super().__init__(f"All 3 agents failed for requirement: {req_id}")


class ScoreParseError(Exception):
    def __init__(self, agent_role: str, raw_response: str):
        self.agent_role = agent_role
        self.raw_response = raw_response
        super().__init__(f"Cannot parse LLM response for {agent_role}: {raw_response}")


class LLMCallError(Exception):
    def __init__(self, agent_role: str, attempt: int, original: Exception):
        self.agent_role = agent_role
        self.attempt = attempt
        self.original = original
        super().__init__(f"LLM call failed for {agent_role} (attempt {attempt}): {original}")


class ReviewAgent:
    ROLE_NAMES = frozenset({"产品分析", "价值评估", "技术可行性"})

    def __init__(self, role_name: str):
        if role_name not in self.ROLE_NAMES:
            raise ValueError(f"Invalid role name: {role_name}")
        self.role_name = role_name

    def call_llm(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement call_llm")

    def _build_prompt(self, requirement: StructuredRequirement) -> str:
        return PROMPT_TEMPLATE.format(
            role_name=self.role_name,
            req_id=requirement.id,
            original_text=requirement.original_text,
            summary=requirement.summary,
        )

    def score(self, requirement: StructuredRequirement) -> DimensionScores:
        prompt = self._build_prompt(requirement)
        try:
            raw = self.call_llm(prompt)
        except Exception as e:
            raise LLMCallError(self.role_name, 0, e)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ScoreParseError(self.role_name, raw)

        try:
            business_value = int(data["business_value"])
            technical_feasibility = int(data["technical_feasibility"])
            roi = int(data["roi"])
            system_compatibility = int(data["system_compatibility"])
            verdict_str = data["verdict"]
        except (KeyError, ValueError, TypeError) as e:
            raise ScoreParseError(self.role_name, raw)

        if not all(1 <= v <= 5 for v in [business_value, technical_feasibility, roi, system_compatibility]):
            raise ScoreParseError(self.role_name, f"Scores out of 1-5 range: {raw}")

        verdict = Verdict(verdict_str)

        return DimensionScores(
            agent_role=self.role_name,
            business_value=business_value,
            technical_feasibility=technical_feasibility,
            roi=roi,
            system_compatibility=system_compatibility,
            verdict=verdict,
            comments=data.get("comments"),
        )


class ReviewTeam:
    MAX_RETRIES = 3
    AGENT_ROLES = ["产品分析", "价值评估", "技术可行性"]

    def __init__(self, session: Session):
        self._session = session
        self._agents = [ReviewAgent(role) for role in self.AGENT_ROLES]

    def _load_requirement(self, req_id: str) -> StructuredRequirement:
        req = self._session.query(Requirements).filter(Requirements.id == req_id).first()
        if req is None:
            raise RequirementNotFoundError(req_id)
        return StructuredRequirement(
            id=req.id,
            original_text=req.original_text,
            summary=req.summary or "",
            submitter_id=req.submitter_id,
            submitter_name=req.submitter_name,
            tags=req.tags if req.tags else [],
            estimated_scope=req.estimated_scope,
            created_at=req.created_at,
        )

    def _persist_score(self, req_id: str, score: DimensionScores) -> None:
        row = ReviewResults(
            requirement_id=req_id,
            agent_role=score.agent_role,
            business_value=score.business_value,
            technical_feasibility=score.technical_feasibility,
            roi=score.roi,
            system_compatibility=score.system_compatibility,
            verdict=score.verdict.value,
            comments=score.comments,
            scored_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        self._session.commit()

    def _notify_agent_failure(self, role_name: str, error: Exception) -> None:
        logger.error("Agent %s failed after retries: %s", role_name, error)

    def _execute_agent(
        self, agent: ReviewAgent, requirement: StructuredRequirement
    ) -> DimensionScores | None:
        return retry_with_backoff(
            lambda: agent.score(requirement),
            max_retries=self.MAX_RETRIES,
            on_exhausted=lambda e: self._notify_agent_failure(agent.role_name, e),
        )

    def run_scoring(self, req_id: str) -> list[DimensionScores]:
        requirement = self._load_requirement(req_id)

        results: list[DimensionScores] = []

        with ThreadPoolExecutor(max_workers=len(self._agents)) as executor:
            future_to_agent = {
                executor.submit(self._execute_agent, agent, requirement): agent
                for agent in self._agents
            }
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                except Exception as e:
                    self._notify_agent_failure(agent.role_name, e)
                    continue
                if result is not None:
                    self._persist_score(req_id, result)
                    results.append(result)

        if not results:
            raise AllAgentsFailedError(req_id)

        return results
