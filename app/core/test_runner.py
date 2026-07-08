"""TestRunner — 实施后的完整测试验收 (F030).

Runs tests and collects coverage via CodeAgentAdapter in the worktree.
Supports capability-based degradation (Capability.RUN_TESTS).
"""

import json
import logging

from pydantic import BaseModel, Field

from app.core.adapters.base import (
    AgentRunResult, Capability, CodeAgentAdapter, OutputContract, TaskSpec, Workspace,
)

logger = logging.getLogger(__name__)

COVERAGE_LINE_THRESHOLD = 80.0
COVERAGE_BRANCH_THRESHOLD = 70.0


class TestResult(BaseModel):
    __test__ = False
    total: int = 0
    passed: int = 0
    failures: list[str] = Field(default_factory=list)
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    degraded: bool = False

    def passed_with_gate(self) -> bool:
        if self.degraded:
            return False
        return (
            self.passed == self.total
            and self.total > 0
            and self.line_coverage >= COVERAGE_LINE_THRESHOLD
            and self.branch_coverage >= COVERAGE_BRANCH_THRESHOLD
        )


class TestRunner:
    __test__ = False

    def __init__(self, adapter: CodeAgentAdapter | None = None):
        self._adapter = adapter

    def can_run_tests(self) -> bool:
        if self._adapter is None:
            return False
        return Capability.RUN_TESTS in self._adapter.capabilities()

    def run_tests(self, workspace: Workspace) -> TestResult:
        if not self.can_run_tests():
            return TestResult(degraded=True)

        task = self._build_task_spec(workspace)
        try:
            result = self._adapter.execute(task, workspace)
        except Exception as e:
            logger.warning("TestRunner execution failed for %s: %s", workspace.req_id, e)
            return TestResult(degraded=True, failures=[str(e)])

        return self._parse_result(result)

    def _build_task_spec(self, workspace: Workspace) -> TaskSpec:
        return TaskSpec(
            role="test_runner",
            objective=f"运行测试并收集覆盖率：{workspace.req_id}",
            stage="test",
            inputs={
                "worktree_path": workspace.path,
                "req_id": workspace.req_id,
                "stage": workspace.stage,
            },
            output_contract=OutputContract(
                structured_fields=["total", "passed", "failures", "line_coverage", "branch_coverage"],
            ),
            constraints=[
                "run all tests (unit + integration) in the worktree",
                "collect line and branch coverage data",
            ],
        )

    @staticmethod
    def _parse_result(result: AgentRunResult) -> TestResult:
        if result.structured:
            data = result.structured
        else:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                return TestResult(degraded=True)

        return TestResult(
            total=data.get("total", 0),
            passed=data.get("passed", 0),
            failures=data.get("failures", []),
            line_coverage=float(data.get("line_coverage", 0.0)),
            branch_coverage=float(data.get("branch_coverage", 0.0)),
            degraded=result.degraded,
        )
