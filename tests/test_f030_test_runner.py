"""Tests for F030: TestRunner 完整测试验收.

Verifies TestResult model, TestRunner adapter delegation,
capability degradation, and ImplementationTeam integration.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.adapters.base import (
    AgentRunResult, Capability, CodeAgentAdapter, TaskSpec, Workspace,
)
from app.core.implementation_team import ImplementationTeam
from app.core.test_runner import (
    COVERAGE_BRANCH_THRESHOLD,
    COVERAGE_LINE_THRESHOLD,
    TestResult,
    TestRunner,
)
from app.models import Base, DesignResults, ImplementationResults, Requirements


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
def mock_adapter():
    adapter = create_autospec(CodeAgentAdapter, instance=True)
    adapter.provider_name = "mock"
    return adapter


def _make_ws(req_id="REQ-TEST-001") -> Workspace:
    return Workspace(path="/tmp/ws/test", req_id=req_id, stage="implementation")


class TestTestResultModel:
    def test_defaults(self):
        tr = TestResult()
        assert tr.total == 0
        assert tr.passed == 0
        assert tr.failures == []
        assert tr.line_coverage == 0.0
        assert tr.branch_coverage == 0.0
        assert tr.degraded is False

    def test_passed_with_gate_all_good(self):
        tr = TestResult(total=10, passed=10, line_coverage=85.0, branch_coverage=75.0)
        assert tr.passed_with_gate() is True

    def test_passed_with_gate_fails_on_failures(self):
        tr = TestResult(total=10, passed=8, failures=["test_a"], line_coverage=85.0, branch_coverage=75.0)
        assert tr.passed_with_gate() is False

    def test_passed_with_gate_fails_low_line_coverage(self):
        tr = TestResult(total=10, passed=10, line_coverage=COVERAGE_LINE_THRESHOLD - 5, branch_coverage=75.0)
        assert tr.passed_with_gate() is False

    def test_passed_with_gate_fails_low_branch_coverage(self):
        tr = TestResult(total=10, passed=10, line_coverage=85.0, branch_coverage=COVERAGE_BRANCH_THRESHOLD - 5)
        assert tr.passed_with_gate() is False

    def test_passed_with_gate_zero_tests(self):
        tr = TestResult(total=0, passed=0, line_coverage=0.0, branch_coverage=0.0)
        assert tr.passed_with_gate() is False

    def test_passed_with_gate_degraded(self):
        tr = TestResult(total=0, passed=0, degraded=True)
        assert tr.passed_with_gate() is False


class TestTestRunnerCanRunTests:
    def test_no_adapter_returns_false(self):
        runner = TestRunner()
        assert runner.can_run_tests() is False

    def test_adapter_with_run_tests_capability(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.RUN_TESTS}
        runner = TestRunner(adapter)
        assert runner.can_run_tests() is True

    def test_adapter_without_run_tests_capability(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.READ_WRITE_FILES}
        runner = TestRunner(adapter)
        assert runner.can_run_tests() is False


class TestTestRunnerBuildTaskSpec:
    def test_task_spec_contains_stage_and_role(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.RUN_TESTS}
        runner = TestRunner(adapter)
        ws = _make_ws()
        task = runner._build_task_spec(ws)
        assert isinstance(task, TaskSpec)
        assert task.role == "test_runner"
        assert task.stage == "test"

    def test_task_spec_has_structured_fields(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.RUN_TESTS}
        runner = TestRunner(adapter)
        ws = _make_ws()
        task = runner._build_task_spec(ws)
        assert "total" in task.output_contract.structured_fields
        assert "line_coverage" in task.output_contract.structured_fields

    def test_task_spec_includes_worktree_path(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.RUN_TESTS}
        runner = TestRunner(adapter)
        ws = _make_ws()
        task = runner._build_task_spec(ws)
        assert task.inputs["worktree_path"] == "/tmp/ws/test"


class TestTestRunnerParseResult:
    def test_parse_structured_result(self):
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "total": 15,
                "passed": 15,
                "failures": [],
                "line_coverage": 92.5,
                "branch_coverage": 85.0,
            },
        )
        tr = TestRunner._parse_result(result)
        assert tr.total == 15
        assert tr.passed == 15
        assert tr.line_coverage == 92.5
        assert tr.branch_coverage == 85.0
        assert tr.degraded is False

    def test_parse_stdout_when_no_structured(self):
        result = AgentRunResult(
            provider="mock", exit_code=0,
            stdout='{"total": 5, "passed": 5, "failures": [], "line_coverage": 100.0, "branch_coverage": 95.0}',
            stderr="",
        )
        tr = TestRunner._parse_result(result)
        assert tr.total == 5
        assert tr.passed == 5

    def test_parse_stdout_malformed_returns_degraded(self):
        result = AgentRunResult(
            provider="mock", exit_code=1, stdout="not json", stderr="error",
        )
        tr = TestRunner._parse_result(result)
        assert tr.degraded is True

    def test_parse_empty_result(self):
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
        )
        tr = TestRunner._parse_result(result)
        assert tr.total == 0
        assert tr.passed == 0

    def test_parse_with_failures(self):
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={
                "total": 10,
                "passed": 7,
                "failures": ["test_login", "test_auth"],
                "line_coverage": 70.0,
                "branch_coverage": 60.0,
            },
        )
        tr = TestRunner._parse_result(result)
        assert tr.total == 10
        assert tr.passed == 7
        assert tr.failures == ["test_login", "test_auth"]

    def test_parse_degraded_flag_from_result(self):
        result = AgentRunResult(
            provider="mock", exit_code=0, stdout='{"total": 0}', stderr="",
            degraded=True,
        )
        tr = TestRunner._parse_result(result)
        assert tr.degraded is True


class TestTestRunnerRunTests:
    def test_no_adapter_returns_degraded(self):
        runner = TestRunner()
        ws = _make_ws()
        tr = runner.run_tests(ws)
        assert tr.degraded is True
        assert tr.passed_with_gate() is False

    def test_adapter_without_capability_returns_degraded(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.READ_WRITE_FILES}
        runner = TestRunner(adapter)
        ws = _make_ws()
        tr = runner.run_tests(ws)
        assert tr.degraded is True
        adapter.execute.assert_not_called()

    def test_adapter_execute_called_with_task_and_ws(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.RUN_TESTS}
        adapter.execute.return_value = AgentRunResult(
            provider="mock", exit_code=0, stdout="", stderr="",
            structured={"total": 5, "passed": 5, "failures": [], "line_coverage": 90.0, "branch_coverage": 80.0},
        )
        runner = TestRunner(adapter)
        ws = _make_ws()
        runner.run_tests(ws)
        adapter.execute.assert_called_once()
        args, _ = adapter.execute.call_args
        task, ws_arg = args
        assert isinstance(task, TaskSpec)
        assert ws_arg is ws

    def test_adapter_execute_error_returns_degraded(self):
        adapter = create_autospec(CodeAgentAdapter, instance=True)
        adapter.capabilities.return_value = {Capability.RUN_TESTS}
        adapter.execute.side_effect = RuntimeError("CLI crash")
        runner = TestRunner(adapter)
        ws = _make_ws()
        tr = runner.run_tests(ws)
        assert tr.degraded is True
        assert len(tr.failures) == 1


class TestImplementationTeamIntegration:
    """Test the TestRunner integration within ImplementationTeam."""

    @pytest.fixture
    def req_with_design(self, db_session):
        req = Requirements(
            id="REQ-20260708-030",
            original_text="集成测试",
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
                document_url="design://v1",
                skeleton_dirs=["src/foo"] if role == "技术选型" else None,
                core_interfaces=[{"method": "bar"}] if role == "技术选型" else None,
                risk_warnings=[],
                created_at=datetime.now(timezone.utc),
                version=1,
            )
            db_session.add(dr)
        db_session.commit()
        return req

    def test_run_implementation_runs_tests_and_persists(self, db_session, req_with_design, mock_adapter):
        mock_adapter.capabilities.return_value = {Capability.RUN_TESTS}

        def _execute_side_effect(task, workspace):
            if task.role == "test_runner":
                return AgentRunResult(
                    provider="mock", exit_code=0, stdout="", stderr="",
                    structured={"total": 10, "passed": 10, "failures": [], "line_coverage": 90.0, "branch_coverage": 85.0},
                )
            return AgentRunResult(
                provider="mock", exit_code=0, stdout="", stderr="",
                structured={
                    "code_files": [{"path": f"src/{task.role}.py", "content": f"# {task.role} code"}],
                    "ambiguity_notes": [],
                },
            )

        mock_adapter.execute.side_effect = _execute_side_effect

        test_runner = TestRunner(adapter=mock_adapter)
        team = ImplementationTeam(
            session=db_session, adapter=mock_adapter,
            test_runner=test_runner,
        )
        team._wm = MagicMock()
        team._wm.acquire_workspace.return_value = _make_ws("REQ-20260708-030")

        result = team.run_implementation("REQ-20260708-030")

        assert result.test_result is not None
        assert result.test_result["total"] == 10
        assert result.test_result["passed"] == 10
        assert result.worktree_path is not None

        row = db_session.query(ImplementationResults).filter(
            ImplementationResults.requirement_id == "REQ-20260708-030"
        ).first()
        assert row is not None
        assert row.test_result is not None
        assert row.test_result["total"] == 10

    def test_run_implementation_skips_tests_when_no_test_runner(self, db_session):
        req = Requirements(
            id="REQ-20260708-031",
            original_text="无 TestRunner",
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
                document_url="design://v1",
                skeleton_dirs=[],
                core_interfaces=[],
                risk_warnings=[],
                created_at=datetime.now(timezone.utc),
                version=1,
            )
            db_session.add(dr)
        db_session.commit()

        team = ImplementationTeam(session=db_session)
        design_doc = {
            "requirement_id": "REQ-20260708-031",
            "original_text": "无 TestRunner",
            "summary": "",
            "design_content": "design",
            "skeleton_dirs": [],
            "core_interfaces": [],
            "risk_warnings": [],
            "version": 1,
        }
        team._load_design_output = MagicMock(return_value=design_doc)

        def _execute_side_effect(agent, doc, _ws=None):
            agent.call_llm = MagicMock(return_value='{"code_files": [], "ambiguity_notes": []}')
            return agent.generate(doc)

        team._execute_agent = _execute_side_effect

        result = team.run_implementation("REQ-20260708-031")
        assert result.test_result is None
        assert result.worktree_path is None
