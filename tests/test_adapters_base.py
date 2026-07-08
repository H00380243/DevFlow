"""Tests for F024: CodeAgentAdapter 抽象与 Registry."""

import pytest
from app.core.adapters.base import (
    Capability, TaskSpec, OutputContract, Workspace, AgentRunResult,
    CodeAgentAdapter, CodeAgentRegistry,
)
from app.core.config import ConfigError


class TestCapability:
    def test_enum_values(self):
        assert Capability.READ_WRITE_FILES.value == "read_write_files"
        assert Capability.RUN_SHELL.value == "run_shell"
        assert Capability.RUN_TESTS.value == "run_tests"
        assert Capability.STRUCTURED_OUTPUT.value == "structured_output"
        assert Capability.WORKTREE_ISOLATION.value == "worktree_isolation"


class TestTaskSpec:
    def test_create_with_defaults(self):
        spec = TaskSpec(role="developer", objective="write code", stage="impl")
        assert spec.role == "developer"
        assert spec.objective == "write code"
        assert spec.stage == "impl"
        assert spec.inputs == {}
        assert spec.output_contract.format == "json"
        assert spec.timeout_sec == 600
        assert spec.constraints == []

    def test_create_with_all_fields(self):
        spec = TaskSpec(
            role="reviewer", objective="review code", stage="review",
            inputs={"req_id": "REQ-001", "summary": "test"},
            output_contract=OutputContract(
                structured_fields=["score", "verdict"],
                artifact_files=["review.json"],
                format="json",
            ),
            timeout_sec=300,
            constraints=["no network"],
        )
        assert spec.inputs["req_id"] == "REQ-001"
        assert spec.output_contract.structured_fields == ["score", "verdict"]
        assert spec.output_contract.artifact_files == ["review.json"]
        assert spec.timeout_sec == 300
        assert spec.constraints == ["no network"]


class TestWorkspace:
    def test_create(self):
        ws = Workspace(path="/tmp/ws", req_id="REQ-001", stage="review")
        assert ws.path == "/tmp/ws"
        assert ws.req_id == "REQ-001"
        assert ws.stage == "review"
        assert ws.base_ref is None

    def test_create_with_base_ref(self):
        ws = Workspace(path="/tmp/ws", req_id="REQ-001", stage="impl", base_ref="main")
        assert ws.base_ref == "main"


class TestAgentRunResult:
    def test_create_with_defaults(self):
        result = AgentRunResult(provider="claude", exit_code=0, stdout="ok", stderr="")
        assert result.provider == "claude"
        assert result.exit_code == 0
        assert result.artifact_paths == []
        assert result.structured is None
        assert result.degraded is False
        assert result.duration_sec == 0.0

    def test_create_degraded(self):
        result = AgentRunResult(
            provider="opencode", exit_code=1, stdout="", stderr="error",
            degraded=True, duration_sec=5.0,
        )
        assert result.degraded is True
        assert result.duration_sec == 5.0


class TestCodeAgentAdapter:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            CodeAgentAdapter()

    def test_concrete_subclass(self):
        class TestAdapter(CodeAgentAdapter):
            @property
            def provider_name(self) -> str:
                return "test"

            def capabilities(self) -> set[Capability]:
                return {Capability.READ_WRITE_FILES}

            def execute(self, task: TaskSpec, workspace: Workspace) -> AgentRunResult:
                return AgentRunResult(provider="test", exit_code=0, stdout="done", stderr="")

        adapter = TestAdapter()
        assert adapter.provider_name == "test"
        assert adapter.capabilities() == {Capability.READ_WRITE_FILES}
        result = adapter.execute(
            TaskSpec(role="tester", objective="test", stage="test"),
            Workspace(path="/tmp", req_id="REQ-001", stage="test"),
        )
        assert result.stdout == "done"


class TestCodeAgentRegistry:
    def test_register_and_get(self):
        class MockAdapter(CodeAgentAdapter):
            @property
            def provider_name(self) -> str:
                return "mock"

            def capabilities(self) -> set[Capability]:
                return set()

            def execute(self, task: TaskSpec, workspace: Workspace) -> AgentRunResult:
                return AgentRunResult(provider="mock", exit_code=0, stdout="", stderr="")

        CodeAgentRegistry.register("mock_test", MockAdapter)
        adapter = CodeAgentRegistry.get("mock_test")
        assert adapter.provider_name == "mock"

    def test_get_unknown_raises(self):
        with pytest.raises(ConfigError, match="Unknown CODE_AGENT_PROVIDER"):
            CodeAgentRegistry.get("nonexistent")

    def test_health_check_unknown_returns_false(self):
        assert CodeAgentRegistry.health_check("nonexistent") is False
