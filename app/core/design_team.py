"""Design Team — F012 设计团多角色产出.

Implements 3-role parallel design agent execution with exponential backoff retry.
v2 (F028): Delegates execution to CodeAgentAdapter via adapter.execute().
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.adapters.base import (
    AgentRunResult, CodeAgentAdapter, OutputContract, TaskSpec, Workspace,
)
from app.core.state_machine import RequirementNotFoundError
from app.core.review_scoring import LLMCallError, retry_with_backoff
from app.core.workspace_manager import WorkspaceManager
from app.models import DesignResults, Requirements, StructuredRequirement

logger = logging.getLogger(__name__)

T = TypeVar("T")

PROMPT_TEMPLATE = (
    "你是一个{role_name}设计专家。请为以下需求进行概要设计。\n\n"
    "需求ID: {req_id}\n"
    "需求描述: {original_text}\n"
    "需求摘要: {summary}\n\n"
    "{role_specific_instructions}"
    "请以JSON格式返回。\n"
    "{role_specific_fields}"
)

ROLE_INSTRUCTIONS = {
    "产品设计": {
        "instructions": (
            "请设计功能边界和用户流程。\n"
        ),
        "fields": (
            '参考格式：\n'
            '{{"document_content": "概要设计文本", "user_flow": "用户流程描述"}}\n'
        ),
    },
    "技术选型": {
        "instructions": (
            "请设计模块划分和技术选型。\n"
        ),
        "fields": (
            '参考格式：\n'
            '{{"skeleton_dirs": ["src/module_a", "src/module_b"], "core_interfaces": [{{"module": "module_a", "method": "method_name", "signature": "def method_name(param: str) -> str"}}]}}\n'
        ),
    },
    "合规风控": {
        "instructions": (
            "请评估合规风险并给出建议。\n"
        ),
        "fields": (
            '参考格式：\n'
            '{{"risk_warnings": ["风险描述"], "recommendations": "建议内容", "has_high_risk": false}}\n'
        ),
    },
}

ROLE_NAMES = frozenset({"产品设计", "技术选型", "合规风控"})


class DesignOutput(BaseModel):
    agent_role: str = Field(..., min_length=1)
    raw_text: str = Field(..., min_length=1)
    document_content: str | None = None
    user_flow: str | None = None
    skeleton_dirs: list[str] = Field(default_factory=list)
    core_interfaces: list[dict] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list)
    recommendations: str | None = None
    has_high_risk: bool = False


class DesignResult(BaseModel):
    requirement_id: str
    document_url: str | None = None
    skeleton_dirs: list[str] = Field(default_factory=list)
    core_interfaces: list[dict] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list)
    version: int = 1


class AllAgentsFailedError(Exception):
    def __init__(self, req_id: str):
        self.req_id = req_id
        super().__init__(f"All 3 design agents failed for requirement: {req_id}")


class DesignParseError(Exception):
    def __init__(self, agent_role: str, raw_response: str):
        self.agent_role = agent_role
        self.raw_response = raw_response
        super().__init__(f"Cannot parse LLM response for {agent_role}: {raw_response}")


class DesignAgent:
    ROLE_NAMES = ROLE_NAMES

    def __init__(self, role_name: str):
        if role_name not in self.ROLE_NAMES:
            raise ValueError(f"Invalid role name: {role_name}")
        self.role_name = role_name

    def call_llm(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement call_llm")

    def _build_prompt(self, requirement: StructuredRequirement) -> str:
        role_info = ROLE_INSTRUCTIONS[self.role_name]
        return PROMPT_TEMPLATE.format(
            role_name=self.role_name,
            req_id=requirement.id,
            original_text=requirement.original_text,
            summary=requirement.summary or "",
            role_specific_instructions=role_info["instructions"],
            role_specific_fields=role_info["fields"],
        )

    def _build_task_spec(self, requirement: StructuredRequirement) -> TaskSpec:
        prompt = self._build_prompt(requirement)
        return TaskSpec(
            role=self.role_name,
            objective=f"概要设计需求 {requirement.id}",
            stage="design",
            inputs={"prompt": prompt, "requirement_id": requirement.id},
            output_contract=OutputContract(
                structured_fields=["document_content", "user_flow",
                                   "skeleton_dirs", "core_interfaces",
                                   "risk_warnings", "recommendations",
                                   "has_high_risk"],
            ),
        )

    def design(self, requirement: StructuredRequirement,
               adapter: CodeAgentAdapter | None = None,
               workspace: Workspace | None = None) -> DesignOutput:
        if adapter is not None and workspace is not None:
            return self._design_via_adapter(requirement, adapter, workspace)
        return self._design_via_llm(requirement)

    def _design_via_adapter(self, requirement: StructuredRequirement,
                            adapter: CodeAgentAdapter,
                            workspace: Workspace) -> DesignOutput:
        task = self._build_task_spec(requirement)
        try:
            result = adapter.execute(task, workspace)
        except Exception as e:
            raise LLMCallError(self.role_name, 0, e)
        return self._parse_result(result)

    def _parse_result(self, result: AgentRunResult) -> DesignOutput:
        if result.structured:
            data = result.structured
        else:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                raise DesignParseError(self.role_name, result.stdout)

        raw = json.dumps(data, ensure_ascii=False)
        if self.role_name == "产品设计":
            doc_content = data.get("document_content", "")
            user_flow = data.get("user_flow", "")
            return DesignOutput(
                agent_role=self.role_name,
                raw_text=raw,
                document_content=doc_content,
                user_flow=user_flow,
            )
        elif self.role_name == "技术选型":
            dirs = data.get("skeleton_dirs", [])
            ifaces = data.get("core_interfaces", [])
            return DesignOutput(
                agent_role=self.role_name,
                raw_text=raw,
                skeleton_dirs=dirs,
                core_interfaces=ifaces,
            )
        elif self.role_name == "合规风控":
            warnings = data.get("risk_warnings", [])
            recs = data.get("recommendations", "")
            high_risk = data.get("has_high_risk", False)
            return DesignOutput(
                agent_role=self.role_name,
                raw_text=raw,
                risk_warnings=warnings,
                recommendations=recs,
                has_high_risk=high_risk,
            )

    def _design_via_llm(self, requirement: StructuredRequirement) -> DesignOutput:
        prompt = self._build_prompt(requirement)
        try:
            raw = self.call_llm(prompt)
        except Exception as e:
            raise LLMCallError(self.role_name, 0, e)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise DesignParseError(self.role_name, raw)

        try:
            if self.role_name == "产品设计":
                doc_content = data["document_content"]
                user_flow = data.get("user_flow", "")
                return DesignOutput(
                    agent_role=self.role_name,
                    raw_text=raw,
                    document_content=doc_content,
                    user_flow=user_flow,
                )
            elif self.role_name == "技术选型":
                dirs = data.get("skeleton_dirs", [])
                ifaces = data.get("core_interfaces", [])
                return DesignOutput(
                    agent_role=self.role_name,
                    raw_text=raw,
                    skeleton_dirs=dirs,
                    core_interfaces=ifaces,
                )
            elif self.role_name == "合规风控":
                warnings = data.get("risk_warnings", [])
                recs = data.get("recommendations", "")
                high_risk = data.get("has_high_risk", False)
                return DesignOutput(
                    agent_role=self.role_name,
                    raw_text=raw,
                    risk_warnings=warnings,
                    recommendations=recs,
                    has_high_risk=high_risk,
                )
        except (KeyError, ValueError, TypeError) as e:
            raise DesignParseError(self.role_name, raw)


class DesignTeam:
    MAX_RETRIES = 3
    AGENT_ROLES = ["产品设计", "技术选型", "合规风控"]

    def __init__(self, session: Session, adapter: CodeAgentAdapter | None = None,
                 workspace_manager: WorkspaceManager | None = None):
        self._session = session
        self._adapter = adapter
        self._wm = workspace_manager
        self._agents = [DesignAgent(role) for role in self.AGENT_ROLES]

    def _load_requirement(self, req_id: str) -> StructuredRequirement:
        req = self._session.query(Requirements).filter(Requirements.id == req_id).first()
        if req is None:
            raise RequirementNotFoundError(req_id)
        return StructuredRequirement(
            id=req.id,
            original_text=req.original_text,
            summary=req.summary or "",
            submitter_id=req.submitter_id,
            submitter_name=req.submitter_name,
            tags=req.tags if req.tags else [],
            estimated_scope=req.estimated_scope,
            created_at=req.created_at,
        )

    def _get_next_version(self, req_id: str) -> int:
        max_version = (
            self._session.query(DesignResults.version)
            .filter(DesignResults.requirement_id == req_id)
            .order_by(DesignResults.version.desc())
            .first()
        )
        if max_version is None:
            return 1
        return max_version[0] + 1

    def _persist_output(self, req_id: str, output: DesignOutput, version: int) -> None:
        row = DesignResults(
            requirement_id=req_id,
            agent_role=output.agent_role,
            document_url=output.document_content or "",
            skeleton_dirs=output.skeleton_dirs if output.skeleton_dirs else None,
            core_interfaces=output.core_interfaces if output.core_interfaces else None,
            risk_warnings=output.risk_warnings if output.risk_warnings else None,
            created_at=datetime.now(timezone.utc),
            version=version,
        )
        self._session.add(row)
        self._session.commit()

    def _notify_agent_failure(self, role_name: str, error: Exception) -> None:
        logger.error("Design Agent %s failed after retries: %s", role_name, error)

    def _execute_agent(
        self, agent: DesignAgent, requirement: StructuredRequirement,
        workspace: Workspace | None = None,
    ) -> DesignOutput | None:
        return retry_with_backoff(
            lambda: agent.design(requirement, self._adapter, workspace),
            max_retries=self.MAX_RETRIES,
            on_exhausted=lambda e: self._notify_agent_failure(agent.role_name, e),
        )

    @staticmethod
    def _aggregate_results(req_id: str, outputs: list[DesignOutput], version: int) -> DesignResult:
        doc_url: str | None = None
        skeleton_dirs: list[str] = []
        core_interfaces: list[dict] = []
        risk_warnings: list[str] = []

        for output in outputs:
            if output.agent_role == "产品设计":
                doc_url = f"design://{req_id}/v{version}"
            elif output.agent_role == "技术选型":
                skeleton_dirs = output.skeleton_dirs
                core_interfaces = output.core_interfaces
            elif output.agent_role == "合规风控":
                for warning in output.risk_warnings:
                    if output.has_high_risk:
                        warning = "[高风险] " + warning
                    risk_warnings.append(warning)

        return DesignResult(
            requirement_id=req_id,
            document_url=doc_url,
            skeleton_dirs=skeleton_dirs,
            core_interfaces=core_interfaces,
            risk_warnings=risk_warnings,
            version=version,
        )

    def run_design(self, req_id: str) -> DesignResult:
        requirement = self._load_requirement(req_id)
        version = self._get_next_version(req_id)

        ws: Workspace | None = None
        if self._adapter is not None or self._wm is not None:
            wm = self._wm or WorkspaceManager()
            ws = wm.acquire_workspace(req_id, "design")

        results: list[DesignOutput] = []

        with ThreadPoolExecutor(max_workers=len(self._agents)) as executor:
            future_to_agent = {
                executor.submit(self._execute_agent, agent, requirement, ws): agent
                for agent in self._agents
            }
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                except Exception as e:
                    self._notify_agent_failure(agent.role_name, e)
                    continue
                if result is not None:
                    self._persist_output(req_id, result, version)
                    results.append(result)

        if ws is not None:
            wm = self._wm or WorkspaceManager()
            wm.release_workspace(req_id, "design")

        if not results:
            raise AllAgentsFailedError(req_id)

        return self._aggregate_results(req_id, results, version)
