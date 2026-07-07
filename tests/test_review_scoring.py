"""Tests for ReviewTeam & ReviewAgent — F008 评审团多角色打分."""

import json
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Base,
    Requirements,
    ReviewResults,
    StructuredRequirement,
)


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
def requirement(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260707-001",
        original_text="用户反馈系统需要增加批量导入功能",
        submitter_id="user001",
        current_stage="review",
        current_status="PENDING_REVIEW",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


@pytest.fixture
def structured_requirement() -> StructuredRequirement:
    return StructuredRequirement(
        id="REQ-20260707-001",
        original_text="用户反馈系统需要增加批量导入功能",
        summary="批量导入功能",
        submitter_id="user001",
    )


class TestReviewAgentScoreHappy:
    """Test B: FUNC/happy — ReviewAgent.score with valid JSON response."""

    def test_score_returns_dimension_scores(self, structured_requirement):
        from app.core.review_scoring import DimensionScores, ReviewAgent, Verdict

        agent = ReviewAgent(role_name="产品分析")
        mock_response = json.dumps({
            "business_value": 5,
            "technical_feasibility": 4,
            "roi": 3,
            "system_compatibility": 5,
            "verdict": "通过",
            "comments": "good",
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.score(structured_requirement)

        assert isinstance(result, DimensionScores)
        assert result.agent_role == "产品分析"
        assert result.business_value == 5
        assert result.technical_feasibility == 4
        assert result.roi == 3
        assert result.system_compatibility == 5
        assert result.verdict == Verdict.APPROVE
        assert result.comments == "good"


class TestReviewAgentScoreBoundaryMin:
    """Test G: BNDRY/edge — all scores at minimum (1)."""

    def test_score_min_boundary(self, structured_requirement):
        from app.core.review_scoring import DimensionScores, ReviewAgent, Verdict

        agent = ReviewAgent(role_name="产品分析")
        mock_response = json.dumps({
            "business_value": 1,
            "technical_feasibility": 1,
            "roi": 1,
            "system_compatibility": 1,
            "verdict": "反对",
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.score(structured_requirement)

        assert result.business_value == 1
        assert result.technical_feasibility == 1
        assert result.roi == 1
        assert result.system_compatibility == 1
        assert result.verdict == Verdict.REJECT


class TestReviewAgentScoreBoundaryMax:
    """Test H: BNDRY/edge — all scores at maximum (5)."""

    def test_score_max_boundary(self, structured_requirement):
        from app.core.review_scoring import DimensionScores, ReviewAgent, Verdict

        agent = ReviewAgent(role_name="产品分析")
        mock_response = json.dumps({
            "business_value": 5,
            "technical_feasibility": 5,
            "roi": 5,
            "system_compatibility": 5,
            "verdict": "通过",
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.score(structured_requirement)

        assert result.business_value == 5
        assert result.technical_feasibility == 5
        assert result.roi == 5
        assert result.system_compatibility == 5
        assert result.verdict == Verdict.APPROVE


class TestReviewAgentVerdictNeutral:
    """Test I: BNDRY/edge — verdict='中立'."""

    def test_verdict_neutral(self, structured_requirement):
        from app.core.review_scoring import DimensionScores, ReviewAgent, Verdict

        agent = ReviewAgent(role_name="产品分析")
        mock_response = json.dumps({
            "business_value": 3,
            "technical_feasibility": 3,
            "roi": 3,
            "system_compatibility": 3,
            "verdict": "中立",
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.score(structured_requirement)

        assert result.verdict == Verdict.NEUTRAL


class TestReviewAgentScoreParseErrorNonJson:
    """Test F: FUNC/error — non-JSON LLM response raises ScoreParseError."""

    def test_non_json_response_raises(self, structured_requirement):
        from app.core.review_scoring import ReviewAgent, ScoreParseError

        agent = ReviewAgent(role_name="产品分析")
        agent.call_llm = MagicMock(return_value="I think the score is good")

        with pytest.raises(ScoreParseError) as excinfo:
            agent.score(structured_requirement)

        assert "产品分析" in str(excinfo.value)
        assert "I think the score is good" in str(excinfo.value)


class TestReviewAgentScoreOutOfRange:
    """Test J: BNDRY/edge — score=0 raises ScoreParseError."""

    def test_score_zero_raises(self, structured_requirement):
        from app.core.review_scoring import ReviewAgent, ScoreParseError

        agent = ReviewAgent(role_name="产品分析")
        mock_response = json.dumps({
            "business_value": 0,
            "technical_feasibility": 2,
            "roi": 3,
            "system_compatibility": 4,
            "verdict": "通过",
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        with pytest.raises(ScoreParseError) as excinfo:
            agent.score(structured_requirement)

        assert "产品分析" in str(excinfo.value)


class TestReviewAgentPromptConstruction:
    """Test M: INTG/llm — verify prompt construction contains role and requirement."""

    def test_prompt_contains_role_and_requirement(self, structured_requirement):
        from app.core.review_scoring import ReviewAgent

        agent = ReviewAgent(role_name="产品分析")
        agent.call_llm = MagicMock(return_value=json.dumps({
            "business_value": 3,
            "technical_feasibility": 3,
            "roi": 3,
            "system_compatibility": 3,
            "verdict": "通过",
        }))

        agent.score(structured_requirement)

        actual_prompt = agent.call_llm.call_args[0][0]
        assert "产品分析" in actual_prompt
        assert "REQ-20260707-001" in actual_prompt
        assert "批量导入功能" in actual_prompt


class TestReviewTeamRunScoringHappy:
    """Test A: FUNC/happy — run_scoring with 3 successful agents."""

    def test_three_agents_all_succeed(self, db_session, requirement, structured_requirement):
        from app.core.review_scoring import DimensionScores, ReviewTeam, Verdict

        team = ReviewTeam(db_session)
        valid_json = json.dumps({
            "business_value": 4,
            "technical_feasibility": 4,
            "roi": 4,
            "system_compatibility": 4,
            "verdict": "通过",
        })

        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=valid_json)

        results = team.run_scoring("REQ-20260707-001")

        assert len(results) == 3
        for ds in results:
            assert isinstance(ds, DimensionScores)
            assert ds.business_value == 4
            assert ds.technical_feasibility == 4
            assert ds.roi == 4
            assert ds.system_compatibility == 4
            assert ds.verdict == Verdict.APPROVE


class TestReviewTeamRetryThenSuccess:
    """Test C: FUNC/error — 2 failures then success on 3rd attempt."""

    def test_retry_then_success(self, db_session, requirement, structured_requirement):
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session)
        agent = team._agents[0]

        success_json = json.dumps({
            "business_value": 4,
            "technical_feasibility": 4,
            "roi": 4,
            "system_compatibility": 4,
            "verdict": "通过",
        })

        call_count = 0

        def flaky_call_llm(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("LLM timeout")
            return success_json

        agent.call_llm = flaky_call_llm
        team._notify_agent_failure = MagicMock()
        original_sleep = time.sleep
        time_sleeps = []

        def mock_sleep(seconds):
            time_sleeps.append(seconds)

        import app.core.review_scoring as rs
        original_sleep_func = rs.time.sleep
        rs.time.sleep = mock_sleep

        try:
            result = team._execute_agent(agent, structured_requirement)
            assert result is not None
            assert result.business_value == 4
            assert call_count == 3
            team._notify_agent_failure.assert_not_called()
        finally:
            rs.time.sleep = original_sleep_func


class TestReviewTeamAllRetriesExhausted:
    """Test D: FUNC/error — 3 consecutive failures, notify and return None."""

    def test_all_retries_exhausted(self, db_session, requirement, structured_requirement):
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session)
        agent = team._agents[0]
        agent.call_llm = MagicMock(side_effect=ConnectionError("LLM down"))
        team._notify_agent_failure = MagicMock()

        import app.core.review_scoring as rs
        original_sleep = rs.time.sleep
        rs.time.sleep = MagicMock()

        try:
            result = team._execute_agent(agent, structured_requirement)
            assert result is None
            assert agent.call_llm.call_count == 3
            team._notify_agent_failure.assert_called_once_with(
                agent.role_name, unittest_mock_any()
            )
        finally:
            rs.time.sleep = original_sleep


class TestReviewTeamAllAgentsFail:
    """Test E: FUNC/error — all 3 agents fail raises AllAgentsFailedError."""

    def test_all_agents_fail_raises(self, db_session, requirement, structured_requirement):
        from app.core.review_scoring import AllAgentsFailedError, ReviewTeam

        team = ReviewTeam(db_session)
        for agent in team._agents:
            agent.call_llm = MagicMock(side_effect=ConnectionError("LLM down"))

        team._notify_agent_failure = MagicMock()

        import app.core.review_scoring as rs
        original_sleep = rs.time.sleep
        rs.time.sleep = MagicMock()

        try:
            with pytest.raises(AllAgentsFailedError) as excinfo:
                team.run_scoring("REQ-20260707-001")
            assert "REQ-20260707-001" in str(excinfo.value)
            assert team._notify_agent_failure.call_count == 3
        finally:
            rs.time.sleep = original_sleep


class TestReviewTeamRequirementNotFound:
    """Test O: FUNC/error — RequirementNotFoundError for non-existent req."""

    def test_requirement_not_found(self, db_session):
        from app.core.state_machine import RequirementNotFoundError
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session)

        with pytest.raises(RequirementNotFoundError):
            team.run_scoring("REQ-NONEXIST-001")


class TestReviewTeamExponentialBackoff:
    """Test K: PERF/perf — verify exponential backoff timing."""

    def test_exponential_backoff_timing(self, db_session, requirement, structured_requirement):
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session)
        agent = team._agents[0]
        fail_msg = json.dumps({"business_value": 6, "technical_feasibility": 4, "roi": 3, "system_compatibility": 4, "verdict": "通过"})
        call_count = 0

        def flaky_call_llm(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("bad score parse")
            return json.dumps({
                "business_value": 4,
                "technical_feasibility": 4,
                "roi": 4,
                "system_compatibility": 4,
                "verdict": "通过",
            })

        agent.call_llm = flaky_call_llm
        team._notify_agent_failure = MagicMock()

        time_sleeps = []

        def mock_sleep(seconds):
            time_sleeps.append(seconds)

        import app.core.review_scoring as rs
        original_sleep = rs.time.sleep
        rs.time.sleep = mock_sleep

        try:
            result = team._execute_agent(agent, structured_requirement)
            assert result is not None
            assert len(time_sleeps) == 2
            assert time_sleeps[0] == pytest.approx(1.0, abs=0.5)
            assert time_sleeps[1] == pytest.approx(2.0, abs=0.5)
        finally:
            rs.time.sleep = original_sleep


class TestReviewTeamIntegrationDb:
    """Test L: INTG/db — verify ReviewResults rows persisted after run_scoring."""

    def test_scores_persisted_to_db(self, db_session, requirement, structured_requirement):
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session)
        valid_json = json.dumps({
            "business_value": 4,
            "technical_feasibility": 5,
            "roi": 3,
            "system_compatibility": 4,
            "verdict": "通过",
        })

        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=valid_json)

        results = team.run_scoring("REQ-20260707-001")

        assert len(results) == 3

        rows = db_session.query(ReviewResults).filter(
            ReviewResults.requirement_id == "REQ-20260707-001"
        ).all()
        assert len(rows) == 3

        roles_found = set()
        for row in rows:
            roles_found.add(row.agent_role)
            assert row.business_value == 4
            assert row.technical_feasibility == 5
            assert row.roi == 3
            assert row.system_compatibility == 4
            assert row.verdict == "通过"

        assert roles_found == {"产品分析", "价值评估", "技术可行性"}


class TestReviewTeamStateMachineIntegration:
    """Test N: INTG/state_machine — F008 does NOT modify state."""

    def test_state_unchanged_after_scoring(self, db_session, requirement, structured_requirement):
        from app.core.state_machine import StateMachine, Status
        from app.core.review_scoring import ReviewTeam

        sm = StateMachine(db_session)
        initial_status = sm.get_status("REQ-20260707-001")
        assert initial_status == Status.PENDING_REVIEW

        team = ReviewTeam(db_session)
        valid_json = json.dumps({
            "business_value": 4,
            "technical_feasibility": 4,
            "roi": 4,
            "system_compatibility": 4,
            "verdict": "通过",
        })

        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=valid_json)

        team.run_scoring("REQ-20260707-001")

        final_status = sm.get_status("REQ-20260707-001")
        assert final_status == Status.PENDING_REVIEW


def unittest_mock_any():
    """Helper for asserting mock was called with any args."""
    from unittest.mock import ANY
    return ANY
