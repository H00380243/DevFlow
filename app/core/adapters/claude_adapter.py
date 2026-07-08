"""F026: ClaudeCodeAdapter — 默认 Code Agent 提供者。"""

import json
import subprocess
import time
from pathlib import Path

from app.core.adapters.base import (
    Capability,
    TaskSpec,
    Workspace,
    AgentRunResult,
    CodeAgentAdapter,
    CodeAgentRegistry,
)


class ClaudeCodeAdapter(CodeAgentAdapter):
    def __init__(self, cli_path: str = "claude", extra_args: list[str] | None = None):
        self._cli = cli_path
        self._extra = extra_args or []

    @property
    def provider_name(self) -> str:
        return "claude"

    def capabilities(self) -> set[Capability]:
        return {
            Capability.READ_WRITE_FILES,
            Capability.RUN_SHELL,
            Capability.RUN_TESTS,
            Capability.STRUCTURED_OUTPUT,
            Capability.WORKTREE_ISOLATION,
        }

    def execute(self, task: TaskSpec, workspace: Workspace) -> AgentRunResult:
        args = [
            self._cli, "-p",
            "--cwd", workspace.path,
            "--output-format", "json",
            "--max-turns", "50",
        ] + self._extra

        prompt = self._render_prompt(task)
        start = time.time()

        try:
            proc = subprocess.run(
                args, input=prompt, capture_output=True,
                text=True, timeout=task.timeout_sec, encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            return AgentRunResult(
                provider=self.provider_name, exit_code=-1,
                stdout="", stderr="Timeout",
                degraded=True, duration_sec=task.timeout_sec,
            )

        duration = time.time() - start
        structured = self._try_parse_json(proc.stdout)
        artifacts = self._scan_artifacts(workspace, task.output_contract)

        return AgentRunResult(
            provider=self.provider_name,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            artifact_paths=artifacts,
            structured=structured,
            degraded=structured is None,
            duration_sec=duration,
        )

    def _render_prompt(self, task: TaskSpec) -> str:
        parts = [
            f"角色：{task.role}",
            f"阶段：{task.stage}",
            f"目标：{task.objective}",
        ]
        if task.inputs:
            parts.append(f"输入：{json.dumps(task.inputs, ensure_ascii=False, indent=2)}")
        if task.output_contract.structured_fields:
            parts.append(
                "请按以下 JSON Schema 输出结构化结果：\n"
                + json.dumps({f: "" for f in task.output_contract.structured_fields}, ensure_ascii=False, indent=2)
            )
        if task.output_contract.artifact_files:
            parts.append(f"请将产物写入以下文件：{', '.join(task.output_contract.artifact_files)}")
        if task.constraints:
            parts.append(f"约束：{'；'.join(task.constraints)}")
        parts.append("请直接输出结果，不要额外解释。")
        return "\n\n".join(parts)

    @staticmethod
    def _try_parse_json(text: str) -> dict | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _scan_artifacts(workspace: Workspace, contract: OutputContract) -> list[str]:
        if not contract.artifact_files:
            return []
        base = Path(workspace.path)
        found = []
        for rel in contract.artifact_files:
            if (base / rel).exists():
                found.append(rel)
        return found


CodeAgentRegistry.register("claude", ClaudeCodeAdapter)
