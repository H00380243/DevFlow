"""CodeAgentEngine — adapter + state machine integration layer.

Orchestrates the full execution pipeline: load requirement → acquire
workspace → build task → execute adapter → drive state machine.
"""

from app.core.adapters.base import (
    CodeAgentAdapter, CodeAgentRegistry, TaskSpec, OutputContract,
    Workspace, AgentRunResult,
)
from app.core.config import get_settings
from app.core.workspace_manager import WorkspaceManager


class CodeAgentEngine:
    """High-level orchestrator that connects adapters, workspaces, and state."""

    def __init__(
        self,
        adapter: CodeAgentAdapter | None = None,
        workspace_manager: WorkspaceManager | None = None,
    ):
        settings = get_settings()
        provider = settings.CODE_AGENT_PROVIDER
        cli_path = settings.CODE_AGENT_CLI_PATH
        timeout = settings.CODE_AGENT_TIMEOUT_SEC
        self._adapter = adapter or CodeAgentRegistry.get(provider, cli_path=cli_path)
        self._wm = workspace_manager or WorkspaceManager()

    def execute(
        self,
        req_id: str,
        stage: str,
        role: str,
        objective: str,
        inputs: dict | None = None,
        output_contract: OutputContract | None = None,
        constraints: list[str] | None = None,
        base_ref: str | None = None,
    ) -> AgentRunResult:
        ws: Workspace | None = None
        try:
            ws = self._wm.acquire_workspace(req_id, stage, base_ref=base_ref)
            task = TaskSpec(
                role=role,
                objective=objective,
                stage=stage,
                inputs=inputs or {},
                output_contract=output_contract or OutputContract(),
                timeout_sec=get_settings().CODE_AGENT_TIMEOUT_SEC,
                constraints=constraints or [],
            )
            return self._adapter.execute(task, ws)
        finally:
            if ws is not None:
                self._wm.release_workspace(req_id, stage)
