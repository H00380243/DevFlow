"""Tests for F027: 评审团委托适配器.

Verifies ReviewTeam/ReviewAgent delegate to CodeAgentAdapter correctly
while preserving backward compatibility.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.adapters.base import (
    AgentRunResult, CodeAgentAdapter, Capability, OutputContract,
    TaskSpec, Workspace,
)
from app.core.review_scoring import (
    DimensionScores, ReviewAgent, ReviewTeam, ScoreParseError, Verdict,
)
from app.models import Base, Requirements, StructuredRequirement


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
def requirement(db_session) -> StructuredRequirement:
    req = Requirements(
        id="REQ-20260708-001",
        original_text="需要增加报表导出功能",
        submitter_id="user001",
        current_stage="review",
        current_status="PENDING_REVIEW",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return StructuredRequirement(
        id=req.id,
        original_text=req.original_text,
        summary="报表导出",
        submitter_id=req.submitter_id,
    )


@pytest.fixture
def requirement() -> StructuredRequirement:
    return StructuredRequirement(
        id="REQ-20260708-001",
        original_text="需要增加报表导出功能",
        summary="报表导出",
        submitter_id="user001",
    )


@pytest.fixture
def mock_adapter():
    adapter = create_autospec(CodeAgentAdapter, instance=True)
    adapter.provider_name = "mock"
    adapter.capabilities.return_value = set(Capability)
    return adapter


def _make_workspace(path: str = "/tmp/ws") -> Workspace:
    return Workspace(path=path, req_id="REQ-20260708-001", stage="review")


class TestReviewAgentBuildTaskSpec:
    """F027: ReviewAgent._build_task_spec produces correct TaskSpec."""

    def test_build_task_spec_contains_role_and_stage(self, requirement):
        agent = ReviewAgent(role_name="产品分析")
        task = agent._build_task_spec(requirement)
        assert isinstance(task, TaskSpec)
        assert task.role == "产品分析"
        assert task.stage == "review"
        assert "REQ-20260708-001" in task.objective

    def test_build_task_spec_has_structured_fields(self, requirement):
        agent = ReviewAgent(role_name="技术可行性")
        task = agent._build_task_spec(requirement)
        fields = task.output_contract.structured_fields
        assert "business_value" in fields
        assert "technical_feasibility" in fields
        assert "roi" in fields
        assert "system_compatibility" in fields
        assert "verdict" in fields
        assert "comments" in fields

    def test_build_task_spec_contains_prompt_in_inputs(self, requirement):
        agent = ReviewAgent(role_name="产品分析")
        task = agent._build_task_spec(requirement)
        assert "prompt" in task.inputs
        assert "产品分析" in task.inputs["prompt"]


class TestReviewAgentParseResult:
    """F027: ReviewAgent._parse_result handles AgentRunResult."""

    def test_parse_structured_output(self, requirement):
        agent = ReviewAgent(role_name="产品分析")
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="",
            stderr="",
            structured={
                "business_value": 4,
                "technical_feasibility": 5,
                "roi": 3,
                "system_compatibility": 4,
                "verdict": "通过",
                "comments": "方案成熟",
            },
        )
        ds = agent._parse_result(result)
        assert isinstance(ds, DimensionScores)
        assert ds.business_value == 4
        assert ds.technical_feasibility == 5
        assert ds.roi == 3
        assert ds.system_compatibility == 4
        assert ds.verdict == Verdict.APPROVE
        assert ds.comments == "方案成熟"

    def test_parse_stdout_when_no_structured(self, requirement):
        agent = ReviewAgent(role_name="价值评估")
        result = AgentRunResult(
            provider="mock", exit_code=0,
            stdout=json.dumps({
                "business_value": 3,
                "technical_feasibility": 3,
                "roi": 3,
                "system_compatibility": 3,
                "verdict": "中立",
            }),
            stderr="",
        )
        ds = agent._parse_result(result)
        assert ds.verdict == Verdict.NEUTRAL
        assert ds.business_value == 3

    def test_parse_stdout_parse_error_raises(self, requirement):
        agent = ReviewAgent(role_name="技术可行性")
        result = AgentRunResult(
            provider="mock", exit_code=0,
            stdout="not json at all",
            stderr="",
        )
        with pytest.raises(ScoreParseError) as excinfo:
            agent._parse_result(result)
        assert "技术可行性" in str(excinfo.value)


class TestReviewAgentScoreViaAdapter:
    """F027: ReviewAgent.score with adapter + workspace."""

    def test_score_via_adapter_returns_dimension_scores(self, requirement, mock_adapter):
        agent = ReviewAgent(role_name="产品分析")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "business_value": 5,
                "technical_feasibility": 4,
                "roi": 4,
                "system_compatibility": 5,
                "verdict": "通过",
            },
        )
        ds = agent.score(requirement, adapter=mock_adapter, workspace=ws)
        assert ds.business_value == 5
        assert ds.verdict == Verdict.APPROVE
        mock_adapter.execute.assert_called_once()

    def test_score_via_adapter_builds_task_spec(self, requirement, mock_adapter):
        agent = ReviewAgent(role_name="价值评估")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "business_value": 3, "technical_feasibility": 4,
                "roi": 3, "system_compatibility": 4,
                "verdict": "通过",
            },
        )
        agent.score(requirement, adapter=mock_adapter, workspace=ws)

        task = mock_adapter.execute.call_args[0][0]
        assert isinstance(task, TaskSpec)
        assert task.role == "价值评估"
        assert task.stage == "review"

    def test_score_via_adapter_passes_workspace(self, requirement, mock_adapter):
        agent = ReviewAgent(role_name="技术可行性")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "business_value": 4, "technical_feasibility": 4,
                "roi": 4, "system_compatibility": 4,
                "verdict": "通过",
            },
        )
        agent.score(requirement, adapter=mock_adapter, workspace=ws)

        passed_ws = mock_adapter.execute.call_args[0][1]
        assert passed_ws.path == "/tmp/ws"

    def test_score_via_adapter_wraps_execution_error(self, requirement, mock_adapter):
        agent = ReviewAgent(role_name="产品分析")
        ws = _make_workspace()
        mock_adapter.execute.side_effect = RuntimeError("CLI crashed")
        with pytest.raises(Exception) as excinfo:
            agent.score(requirement, adapter=mock_adapter, workspace=ws)
        assert "产品分析" in str(excinfo.value)

    def test_score_via_adapter_handles_degraded(self, requirement, mock_adapter):
        agent = ReviewAgent(role_name="产品分析")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=1, stdout="", stderr="err",
            degraded=True,
            structured={
                "business_value": 3, "technical_feasibility": 3,
                "roi": 3, "system_compatibility": 3,
                "verdict": "中立",
            },
        )
        ds = agent.score(requirement, adapter=mock_adapter, workspace=ws)
        assert ds.business_value == 3
        assert ds.verdict == Verdict.NEUTRAL


class TestReviewTeamWithAdapter:
    """F027: ReviewTeam.run_scoring with adapter integration."""

    def _create_req(self, db_session):
        req = Requirements(
            id="REQ-20260708-001",
            original_text="需要增加报表导出功能",
            submitter_id="user001",
            current_stage="review",
            current_status="PENDING_REVIEW",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(req)
        db_session.commit()

    def test_run_scoring_with_mock_adapter(self, db_session, mock_adapter):
        self._create_req(db_session)
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session, adapter=mock_adapter)
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "business_value": 4, "technical_feasibility": 4,
                "roi": 3, "system_compatibility": 4,
                "verdict": "通过",
            },
        )

        team._wm = MagicMock()
        ws = MagicMock()
        team._wm.acquire_workspace.return_value = ws

        results = team.run_scoring("REQ-20260708-001")
        assert len(results) == 3
        for ds in results:
            assert ds.business_value == 4

    def test_run_scoring_with_adapter_failover(self, db_session, mock_adapter):
        self._create_req(db_session)
        from app.core.review_scoring import ReviewTeam

        team = ReviewTeam(db_session, adapter=mock_adapter)
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "business_value": 4, "technical_feasibility": 4,
                "roi": 3, "system_compatibility": 4,
                "verdict": "通过",
            },
        )
        team._wm = MagicMock()
        team._wm.acquire_workspace.return_value = _make_workspace()

        results = team.run_scoring("REQ-20260708-001")
        assert len(results) == 3


class TestCodeAgentEngine:
    """F027: CodeAgentEngine integration helper."""

    def test_execute_calls_adapter(self, mock_adapter):
        from app.core.adapters.engine import CodeAgentEngine
        import app.core.config
        app.core.config.get_settings = MagicMock(return_value=MagicMock(
            CODE_AGENT_PROVIDER="mock",
            CODE_AGENT_CLI_PATH="mock",
            CODE_AGENT_TIMEOUT_SEC=600,
        ))

        mock_wm = MagicMock()
        mock_ws = MagicMock()
        mock_wm.acquire_workspace.return_value = mock_ws
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="ok", stderr="",
        )

        engine = CodeAgentEngine(adapter=mock_adapter, workspace_manager=mock_wm)
        result = engine.execute("REQ-001", "review", "产品分析", "评审需求")

        assert result.exit_code == 0
        mock_adapter.execute.assert_called_once()
        mock_wm.acquire_workspace.assert_called_once_with("REQ-001", "review", base_ref=None)

    def test_execute_cleans_up_workspace(self, mock_adapter):
        from app.core.adapters.engine import CodeAgentEngine
        import app.core.config
        app.core.config.get_settings = MagicMock(return_value=MagicMock(
            CODE_AGENT_PROVIDER="mock",
            CODE_AGENT_CLI_PATH="mock",
            CODE_AGENT_TIMEOUT_SEC=600,
        ))

        mock_wm = MagicMock()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="ok", stderr="",
        )

        engine = CodeAgentEngine(adapter=mock_adapter, workspace_manager=mock_wm)
        engine.execute("REQ-001", "design", "技术选型", "设计评审")

        mock_wm.release_workspace.assert_called_once_with("REQ-001", "design")
