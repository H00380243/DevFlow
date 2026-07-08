"""Tests for F029: 实施团委托适配器.

Verifies ImplementationTeam/ImplementationAgent delegate to CodeAgentAdapter
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
from app.core.implementation_team import (
    CodeOutput, ImplementationAgent, ImplementationTeam, CodeParseError,
)
from app.models import Base, DesignResults, Requirements


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
def design_doc() -> dict:
    return {
        "requirement_id": "REQ-20260708-003",
        "original_text": "实现通知推送服务",
        "summary": "通知推送",
        "design_content": "推送服务概要设计",
        "skeleton_dirs": ["src/push", "src/queue"],
        "core_interfaces": [{"module": "push", "method": "send_notification"}],
        "risk_warnings": [],
        "version": 1,
    }


@pytest.fixture
def mock_adapter():
    adapter = create_autospec(CodeAgentAdapter, instance=True)
    adapter.provider_name = "mock"
    adapter.capabilities.return_value = set(Capability)
    return adapter


def _make_workspace() -> Workspace:
    return Workspace(path="/tmp/ws", req_id="REQ-20260708-003", stage="implementation")


def _create_req(db_session):
    req = Requirements(
        id="REQ-20260708-003",
        original_text="实现通知推送服务",
        submitter_id="user001",
        current_stage="implementation",
        current_status="IN_IMPLEMENTATION",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    for role in ["产品设计", "技术选型", "合规风控"]:
        dr = DesignResults(
            requirement_id=req.id,
            agent_role=role,
            document_url="design://REQ-20260708-003/v1",
            skeleton_dirs=["src/push"] if role == "技术选型" else None,
            core_interfaces=[{"module": "push", "method": "send"}] if role == "技术选型" else None,
            risk_warnings=[],
            created_at=datetime.now(timezone.utc),
            version=1,
        )
        db_session.add(dr)
    db_session.commit()


class TestImplementationAgentBuildTaskSpec:
    def test_build_task_spec_contains_role_and_stage(self, design_doc):
        agent = ImplementationAgent(role_name="后端开发")
        task = agent._build_task_spec(design_doc)
        assert isinstance(task, TaskSpec)
        assert task.role == "后端开发"
        assert task.stage == "implementation"

    def test_build_task_spec_has_structured_fields(self, design_doc):
        agent = ImplementationAgent(role_name="质量保障")
        task = agent._build_task_spec(design_doc)
        assert "code_files" in task.output_contract.structured_fields
        assert "ambiguity_notes" in task.output_contract.structured_fields


class TestImplementationAgentParseResult:
    def test_parse_structured_output(self, design_doc):
        agent = ImplementationAgent(role_name="后端开发")
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "code_files": [{"path": "src/main.py", "content": "def main(): pass"}],
                "ambiguity_notes": [],
            },
        )
        output = agent._parse_result(result)
        assert isinstance(output, CodeOutput)
        assert len(output.code_files) == 1
        assert output.code_files[0]["path"] == "src/main.py"

    def test_parse_missing_code_files_raises(self, design_doc):
        agent = ImplementationAgent(role_name="前端开发")
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout=json.dumps({"ambiguity_notes": []}),
            stderr="",
        )
        with pytest.raises(CodeParseError) as excinfo:
            agent._parse_result(result)
        assert "前端开发" in str(excinfo.value)

    def test_parse_stdout_when_no_structured(self, design_doc):
        agent = ImplementationAgent(role_name="质量保障")
        result = AgentRunResult(
            provider="mock", exit_code=0,
            stdout=json.dumps({
                "code_files": [{"path": "tests/test.py", "content": "def test(): pass"}],
                "ambiguity_notes": [],
            }),
            stderr="",
        )
        output = agent._parse_result(result)
        assert output.code_files[0]["path"] == "tests/test.py"


class TestImplementationAgentGenerateViaAdapter:
    def test_generate_via_adapter_returns_code_output(self, design_doc, mock_adapter):
        agent = ImplementationAgent(role_name="后端开发")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "code_files": [{"path": "src/api.py", "content": "# code"}],
                "ambiguity_notes": [],
            },
        )
        output = agent.generate(design_doc, adapter=mock_adapter, workspace=ws)
        assert output.agent_role == "后端开发"
        mock_adapter.execute.assert_called_once()

    def test_generate_via_adapter_builds_task_spec(self, design_doc, mock_adapter):
        agent = ImplementationAgent(role_name="前端开发")
        ws = _make_workspace()
        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"code_files": [], "ambiguity_notes": []},
        )
        agent.generate(design_doc, adapter=mock_adapter, workspace=ws)
        task = mock_adapter.execute.call_args[0][0]
        assert task.role == "前端开发"
        assert task.stage == "implementation"

    def test_generate_via_adapter_wraps_error(self, design_doc, mock_adapter):
        agent = ImplementationAgent(role_name="质量保障")
        ws = _make_workspace()
        mock_adapter.execute.side_effect = RuntimeError("CLI crash")
        with pytest.raises(Exception) as excinfo:
            agent.generate(design_doc, adapter=mock_adapter, workspace=ws)
        assert "质量保障" in str(excinfo.value)


class TestImplementationTeamWithAdapter:
    def test_run_implementation_with_mock_adapter(self, db_session, design_doc, mock_adapter):
        _create_req(db_session)
        team = ImplementationTeam(session=db_session, adapter=mock_adapter)
        team._wm = MagicMock()
        team._wm.acquire_workspace.return_value = _make_workspace()
        team._load_design_output = MagicMock(return_value=design_doc)

        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "code_files": [{"path": "src/main.py", "content": "# code"}],
                "ambiguity_notes": [],
            },
        )
        result = team.run_implementation("REQ-20260708-003")
        assert result.requirement_id == "REQ-20260708-003"
        assert len(result.code_files) == 1
        assert result.code_files[0]["path"] == "src/main.py"

    def test_run_implementation_passes_workspace(self, db_session, design_doc, mock_adapter):
        _create_req(db_session)
        team = ImplementationTeam(session=db_session, adapter=mock_adapter)
        team._wm = MagicMock()
        team._wm.acquire_workspace.return_value = _make_workspace()
        team._load_design_output = MagicMock(return_value=design_doc)

        mock_adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"code_files": [], "ambiguity_notes": ["设计模糊"]},
        )
        result = team.run_implementation("REQ-20260708-003")
        assert "设计模糊" in result.ambiguity_notes
