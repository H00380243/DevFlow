"""Tests for F026: ClaudeCodeAdapter."""

import json

import pytest

from app.core.adapters.base import (
    Capability, TaskSpec, Workspace, OutputContract,
)
from app.core.adapters.claude_adapter import ClaudeCodeAdapter


class TestClaudeCodeAdapter:
    def test_provider_name(self):
        adapter = ClaudeCodeAdapter()
        assert adapter.provider_name == "claude"

    def test_capabilities(self):
        adapter = ClaudeCodeAdapter()
        caps = adapter.capabilities()
        assert Capability.READ_WRITE_FILES in caps
        assert Capability.RUN_SHELL in caps
        assert Capability.RUN_TESTS in caps
        assert Capability.STRUCTURED_OUTPUT in caps
        assert Capability.WORKTREE_ISOLATION in caps

    def test_render_prompt_basic(self):
        adapter = ClaudeCodeAdapter()
        task = TaskSpec(role="developer", objective="write a function", stage="impl")
        prompt = adapter._render_prompt(task)
        assert "角色：developer" in prompt
        assert "阶段：impl" in prompt
        assert "目标：write a function" in prompt
        assert "不要额外解释" in prompt

    def test_render_prompt_with_inputs_and_fields(self):
        adapter = ClaudeCodeAdapter()
        task = TaskSpec(
            role="reviewer", objective="score this requirement", stage="review",
            inputs={"req_id": "REQ-001", "summary": "login module"},
            output_contract=OutputContract(
                structured_fields=["business_value", "verdict"],
                artifact_files=["review.json"],
            ),
            constraints=["no network"],
        )
        prompt = adapter._render_prompt(task)
        assert "角色：reviewer" in prompt
        assert "REQ-001" in prompt
        assert "business_value" in prompt
        assert "verdict" in prompt
        assert "review.json" in prompt
        assert "no network" in prompt

    def test_try_parse_json_valid(self):
        data = {"score": 4, "verdict": "通过"}
        result = ClaudeCodeAdapter._try_parse_json(json.dumps(data))
        assert result == data

    def test_try_parse_json_invalid(self):
        result = ClaudeCodeAdapter._try_parse_json("not json")
        assert result is None

    def test_try_parse_json_empty(self):
        result = ClaudeCodeAdapter._try_parse_json("")
        assert result is None

    def test_scan_artifacts_none(self, tmp_path):
        ws = Workspace(path=str(tmp_path), req_id="REQ-001", stage="test")
        contract = OutputContract()
        found = ClaudeCodeAdapter._scan_artifacts(ws, contract)
        assert found == []

    def test_scan_artifacts_found(self, tmp_path):
        (tmp_path / "output.json").write_text("{}", encoding="utf-8")
        ws = Workspace(path=str(tmp_path), req_id="REQ-001", stage="test")
        contract = OutputContract(artifact_files=["output.json", "missing.txt"])
        found = ClaudeCodeAdapter._scan_artifacts(ws, contract)
        assert found == ["output.json"]

    def test_execute_timeout(self):
        adapter = ClaudeCodeAdapter(cli_path="python")
        task = TaskSpec(
            role="tester", objective="test", stage="test",
            timeout_sec=1,
        )
        ws = Workspace(path=".", req_id="REQ-001", stage="test")
        result = adapter.execute(task, ws)
        assert result.degraded is True
