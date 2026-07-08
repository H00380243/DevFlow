"""F024: CodeAgentAdapter 抽象基类与数据契约。"""

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.core.config import ConfigError


class Capability(str, Enum):
    READ_WRITE_FILES = "read_write_files"
    RUN_SHELL = "run_shell"
    RUN_TESTS = "run_tests"
    STRUCTURED_OUTPUT = "structured_output"
    WORKTREE_ISOLATION = "worktree_isolation"


class OutputContract(BaseModel):
    structured_fields: list[str] | None = None
    artifact_files: list[str] | None = None
    format: Literal["json", "markdown", "text"] = "json"


class TaskSpec(BaseModel):
    role: str
    objective: str
    stage: str
    inputs: dict = {}
    output_contract: OutputContract = OutputContract()
    timeout_sec: int = 600
    constraints: list[str] = []


class Workspace(BaseModel):
    path: str
    req_id: str
    stage: str
    base_ref: str | None = None


class AgentRunResult(BaseModel):
    provider: str
    exit_code: int
    stdout: str
    stderr: str
    artifact_paths: list[str] = []
    structured: dict | None = None
    degraded: bool = False
    duration_sec: float = 0.0


class CodeAgentAdapter(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def capabilities(self) -> set[Capability]: ...

    @abstractmethod
    def execute(self, task: TaskSpec, workspace: Workspace) -> AgentRunResult: ...


class CodeAgentRegistry:
    _adapters: dict[str, type[CodeAgentAdapter]] = {}

    @classmethod
    def register(cls, provider: str, adapter_cls: type[CodeAgentAdapter]) -> None:
        cls._adapters[provider] = adapter_cls

    @classmethod
    def get(cls, provider: str, **kwargs) -> CodeAgentAdapter:
        if provider not in cls._adapters:
            raise ConfigError(f"Unknown CODE_AGENT_PROVIDER: {provider}")
        return cls._adapters[provider](**kwargs)

    @classmethod
    def health_check(cls, provider: str) -> bool:
        adapter_cls = cls._adapters.get(provider)
        if not adapter_cls:
            return False
        adapter = adapter_cls()
        try:
            import subprocess
            result = subprocess.run(
                [adapter.provider_name, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
