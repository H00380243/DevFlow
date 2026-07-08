"""Code Agent 适配层 — 可插拔执行引擎"""

from app.core.adapters.base import (
    Capability,
    TaskSpec,
    OutputContract,
    Workspace,
    AgentRunResult,
    CodeAgentAdapter,
    CodeAgentRegistry,
)

__all__ = [
    "Capability",
    "TaskSpec",
    "OutputContract",
    "Workspace",
    "AgentRunResult",
    "CodeAgentAdapter",
    "CodeAgentRegistry",
]
