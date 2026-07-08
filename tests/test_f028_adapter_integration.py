"""Tests for F028: 设计团委托适配器.

Verifies DesignTeam/DesignAgent delegate to CodeAgentAdapter correctly
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
from app.core.design_team import (
    DesignAgent, DesignOutput, DesignTeam, DesignParseError,
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
def requirement(db_session):
    req = Requirements(
        id="REQ-20260708-002",
        original_text="实现实时数据看板系统",
        submitter_id="user001",
        current_stage="design",
        current_status="IN_DESIGN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return StructuredRequirement(
        id=req.id,
        original_text=req.original_text,
        summary="实时数据看板",
        submitter_id=req.submitter_id,
    )


@pytest.fixture
def mock_adapter():
    adapter = create_autospec(CodeAgentAdapter, instance=True)
    adapter.provider_name = "mock"
    adapter.capabilities.return_value = set(Capability)
    return adapter


def _make_workspace(path: str = "/tmp/ws") -> Workspace:
    return Workspace(path=path, req_id="REQ-20260708-002", stage="design")


class TestDesignAgentBuildTaskSpec:
    def test_build_task_spec_contains_role_and_stage(self, requirement):
        agent = DesignAgent(role_name="产品设计")
        task = agent._build_task_spec(requirement)
        assert isinstance(task, TaskSpec)
        assert task.role == "产品设计"
        assert task.stage == "design"

    def test_build_task_spec_has_structured_fields(self, requirement):
        agent = DesignAgent(role_name="技术选型")
        task = agent._build_task_spec(requirement)
        fields = task.output_contract.structured_fields
        assert "skeleton_dirs" in fields
        assert "core_interfaces" in fields


class TestDesignAgentParseResult:
    def test_parse_product_design(self, requirement):
        agent = DesignAgent(role_name="产品设计")
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "document_content": "看板概要设计",
                "user_flow": "登录→看板展示",
            },
        )
        output = agent._parse_result(result)
        assert isinstance(output, DesignOutput)
        assert output.document_content == "看板概要设计"
        assert output.user_flow == "登录→看板展示"

    def test_parse_tech_selection(self, requirement):
        agent = DesignAgent(role_name="技术选型")
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "skeleton_dirs": ["src/dashboard", "src/api"],
                "core_interfaces": [{"module": "api", "method": "get_data"}],
            },
        )
        output = agent._parse_result(result)
        assert output.skeleton_dirs == ["src/dashboard", "src/api"]
        assert len(output.core_interfaces) == 1

    def test_parse_compliance_high_risk(self, requirement):
        agent = DesignAgent(role_name="合规风控")
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "risk_warnings": ["数据隐私风险"],
                "recommendations": "需要脱敏",
                "has_high_risk": True,
            },
        )
        output = agent._parse_result(result)
        assert output.has_high_risk is True
        assert "数据隐私风险" in output.risk_warnings

    def test_parse_stdout_when_no_structured(self, requirement):
        agent = DesignAgent(role_name="产品设计")
        result = AgentRunResult(
            provider="mock", exit_code=0,
            stdout=json.dumps({"document_content": "doc", "user_flow": "flow"}),
            stderr="",
        )
        output = agent._parse_result(result)
        assert output.document_content == "doc"


class TestDesignAgentDesignViaAdapter:
    def test_design_via_adapter_returns_design_output(self, requirement, mock_adapter):
        agent = DesignAgent(role_name="产品设计")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"document_content": "设计文档", "user_flow": "flow"},
        )
        output = agent.design(requirement, adapter=mock_adapter, workspace=ws)
        assert output.document_content == "设计文档"
        mock_adapter.execute.assert_called_once()

    def test_design_via_adapter_builds_task_spec(self, requirement, mock_adapter):
        agent = DesignAgent(role_name="合规风控")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"risk_warnings": [], "has_high_risk": False},
        )
        agent.design(requirement, adapter=mock_adapter, workspace=ws)
        task = mock_adapter.execute.call_args[0][0]
        assert task.role == "合规风控"
        assert task.stage == "design"

    def test_design_via_adapter_wraps_execution_error(self, requirement, mock_adapter):
        agent = DesignAgent(role_name="技术选型")
        ws = _make_workspace()
        mock_adapter.execute.side_effect = RuntimeError("CLI crash")
        with pytest.raises(Exception) as excinfo:
            agent.design(requirement, adapter=mock_adapter, workspace=ws)
        assert "技术选型" in str(excinfo.value)


class TestDesignTeamWithAdapter:
    def _create_req(self, db_session):
        req = Requirements(
            id="REQ-20260708-002",
            original_text="实现实时数据看板系统",
            submitter_id="user001",
            current_stage="design",
            current_status="IN_DESIGN",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(req)
        db_session.commit()

    def test_run_design_with_mock_adapter(self, db_session, mock_adapter):
        self._create_req(db_session)
        team = DesignTeam(db_session, adapter=mock_adapter)
        team._wm = MagicMock()
        team._wm.acquire_workspace.return_value = _make_workspace()

        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"document_content": "doc", "user_flow": ""},
        )
        results = team.run_design("REQ-20260708-002")
        assert results is not None
        assert results.requirement_id == "REQ-20260708-002"

    def test_run_design_passes_workspace(self, db_session, mock_adapter):
        self._create_req(db_session)
        team = DesignTeam(db_session, adapter=mock_adapter)
        team._wm = MagicMock()
        team._wm.acquire_workspace.return_value = _make_workspace()

        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"risk_warnings": [], "has_high_risk": False},
        )
        result = team.run_design("REQ-20260708-002")
        assert result.risk_warnings == []
