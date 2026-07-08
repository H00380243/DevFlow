"""Implementation Team — F015 实施团代码生成.

Implements 3-role parallel code generation agent execution with exponential backoff retry.
v2 (F029): Delegates execution to CodeAgentAdapter via adapter.execute().
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
from app.core.review_scoring import LLMCallError
from app.core.test_runner import TestResult, TestRunner
from app.core.workspace_manager import WorkspaceManager
from app.models import DesignResults, ImplementationResults, Requirements

logger = logging.getLogger(__name__)

T = TypeVar("T")

PROMPT_TEMPLATE = (
    "你是一个{role_name}开发专家。请根据以下设计文档生成源代码。\n\n"
    "需求ID: {req_id}\n"
    "需求描述: {original_text}\n"
    "需求摘要: {summary}\n\n"
    "概要设计: {design_content}\n"
    "代码目录骨架: {skeleton_dirs}\n"
    "核心接口定义: {core_interfaces}\n"
    "风险警告: {risk_warnings}\n\n"
    "{role_specific_instructions}"
    "请以JSON格式返回。\n"
    '{{"code_files": [{{"path": "文件路径", "content": "源代码内容"}}], '
    '"ambiguity_notes": ["歧义假设标注"]}}\n'
)

ROLE_INSTRUCTIONS = {
    "后端开发": {
        "instructions": (
            "请按照代码目录骨架和接口定义生成后端源代码文件。"
            "每个文件应包含完整的函数/类实现。\n"
        ),
    },
    "前端开发": {
        "instructions": (
            "请按照概要设计和接口定义生成前端源代码文件。"
            "确保前端组件与后端接口匹配。\n"
        ),
    },
    "质量保障": {
        "instructions": (
            "请生成单元测试和集成测试代码。"
            "测试应覆盖核心接口的 happy path 和边界条件。"
            "如果设计文档存在歧义，请在 ambiguity_notes 中标注假设。\n"
        ),
    },
}

AGENT_ROLES = frozenset({"后端开发", "前端开发", "质量保障"})


class CodeOutput(BaseModel):
    agent_role: str = Field(..., min_length=1)
    raw_text: str = Field(..., min_length=1)
    code_files: list[dict] = Field(default_factory=list)
    ambiguity_notes: list[str] = Field(default_factory=list)


class CodeResult(BaseModel):
    requirement_id: str
    code_files: list[dict] = Field(default_factory=list)
    ambiguity_notes: list[str] = Field(default_factory=list)
    test_result: dict | None = None
    worktree_path: str | None = None


class CodeParseError(Exception):
    def __init__(self, agent_role: str, raw_response: str):
        self.agent_role = agent_role
        self.raw_response = raw_response
        super().__init__(f"Cannot parse LLM response for {agent_role}: {raw_response}")


class AllAgentsFailedError(Exception):
    def __init__(self, req_id: str):
        self.req_id = req_id
        super().__init__(f"All 3 implementation agents failed for requirement: {req_id}")


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    on_exhausted: Callable[[Exception], None] | None = None,
) -> T | None:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except (LLMCallError, CodeParseError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    if on_exhausted and last_error is not None:
        on_exhausted(last_error)
    return None


class ImplementationAgent:
    ROLE_NAMES = AGENT_ROLES

    def __init__(self, role_name: str):
        if role_name not in self.ROLE_NAMES:
            raise ValueError(f"Invalid role name: {role_name}")
        self.role_name = role_name

    def call_llm(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement call_llm")

    def _build_prompt(self, design_doc: dict) -> str:
        role_info = ROLE_INSTRUCTIONS[self.role_name]
        return PROMPT_TEMPLATE.format(
            role_name=self.role_name,
            req_id=design_doc.get("requirement_id", ""),
            original_text=design_doc.get("original_text", ""),
            summary=design_doc.get("summary", ""),
            design_content=design_doc.get("design_content", ""),
            skeleton_dirs=json.dumps(design_doc.get("skeleton_dirs", []), ensure_ascii=False),
            core_interfaces=json.dumps(design_doc.get("core_interfaces", []), ensure_ascii=False),
            risk_warnings=json.dumps(design_doc.get("risk_warnings", []), ensure_ascii=False),
            role_specific_instructions=role_info["instructions"],
        )

    def _build_task_spec(self, design_doc: dict) -> TaskSpec:
        prompt = self._build_prompt(design_doc)
        return TaskSpec(
            role=self.role_name,
            objective=f"生成代码：{design_doc.get('requirement_id', '')}",
            stage="implementation",
            inputs={
                "prompt": prompt,
                "requirement_id": design_doc.get("requirement_id", ""),
                "design_content": design_doc.get("design_content", ""),
                "skeleton_dirs": design_doc.get("skeleton_dirs", []),
            },
            output_contract=OutputContract(
                structured_fields=["code_files", "ambiguity_notes"],
            ),
        )

    def generate(self, design_doc: dict,
                 adapter: CodeAgentAdapter | None = None,
                 workspace: Workspace | None = None) -> CodeOutput:
        if adapter is not None and workspace is not None:
            return self._generate_via_adapter(design_doc, adapter, workspace)
        return self._generate_via_llm(design_doc)

    def _generate_via_adapter(self, design_doc: dict,
                              adapter: CodeAgentAdapter,
                              workspace: Workspace) -> CodeOutput:
        task = self._build_task_spec(design_doc)
        try:
            result = adapter.execute(task, workspace)
        except Exception as e:
            raise LLMCallError(self.role_name, 0, e)
        return self._parse_result(result)

    def _parse_result(self, result: AgentRunResult) -> CodeOutput:
        if result.structured:
            data = result.structured
        else:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                raise CodeParseError(self.role_name, result.stdout)

        if "code_files" not in data:
            raise CodeParseError(self.role_name, json.dumps(data, ensure_ascii=False))
        code_files = data["code_files"]
        for file in code_files:
            _ = file["path"]
            _ = file["content"]
        ambiguity_notes = data.get("ambiguity_notes", [])
        return CodeOutput(
            agent_role=self.role_name,
            raw_text=json.dumps(data, ensure_ascii=False),
            code_files=code_files,
            ambiguity_notes=ambiguity_notes,
        )

    def _generate_via_llm(self, design_doc: dict) -> CodeOutput:
        prompt = self._build_prompt(design_doc)
        try:
            raw = self.call_llm(prompt)
        except Exception as e:
            raise LLMCallError(self.role_name, 0, e)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise CodeParseError(self.role_name, raw)

        try:
            if "code_files" not in data:
                raise CodeParseError(self.role_name, raw)
            code_files = data["code_files"]
            for file in code_files:
                _ = file["path"]
                _ = file["content"]
            ambiguity_notes = data.get("ambiguity_notes", [])
            return CodeOutput(
                agent_role=self.role_name,
                raw_text=raw,
                code_files=code_files,
                ambiguity_notes=ambiguity_notes,
            )
        except (KeyError, TypeError, ValueError):
            raise CodeParseError(self.role_name, raw)


class ImplementationTeam:
    MAX_RETRIES = 3
    AGENT_ROLES = ["后端开发", "前端开发", "质量保障"]

    def __init__(self, session: Session, adapter: CodeAgentAdapter | None = None,
                 workspace_manager: WorkspaceManager | None = None,
                 test_runner: TestRunner | None = None):
        self._session = session
        self._adapter = adapter
        self._wm = workspace_manager
        self._test_runner = test_runner
        self._agents = [ImplementationAgent(role) for role in self.AGENT_ROLES]

    def _load_design_output(self, req_id: str) -> dict:
        req = self._session.query(Requirements).filter(Requirements.id == req_id).first()
        if req is None:
            raise RequirementNotFoundError(req_id)

        max_version = (
            self._session.query(DesignResults.version)
            .filter(DesignResults.requirement_id == req_id)
            .order_by(DesignResults.version.desc())
            .first()
        )
        if max_version is None:
            raise RequirementNotFoundError(f"No design outputs for {req_id}")

        version = max_version[0]
        outputs = (
            self._session.query(DesignResults)
            .filter(
                DesignResults.requirement_id == req_id,
                DesignResults.version == version,
            )
            .all()
        )

        design_content = ""
        skeleton_dirs: list[str] = []
        core_interfaces: list[dict] = []
        risk_warnings: list[str] = []

        for output in outputs:
            if output.agent_role == "产品设计":
                design_content = output.document_url or ""
            elif output.agent_role == "技术选型":
                skeleton_dirs = output.skeleton_dirs or []
                core_interfaces = output.core_interfaces or []
            elif output.agent_role == "合规风控":
                risk_warnings = output.risk_warnings or []

        return {
            "requirement_id": req_id,
            "original_text": req.original_text,
            "summary": req.summary or "",
            "design_content": design_content,
            "skeleton_dirs": skeleton_dirs,
            "core_interfaces": core_interfaces,
            "risk_warnings": risk_warnings,
            "version": version,
        }

    def _persist_output(self, req_id: str, code_files: list[dict],
                        test_result: dict | None = None,
                        worktree_path: str | None = None) -> None:
        row = ImplementationResults(
            requirement_id=req_id,
            code_files=code_files if code_files else [],
            test_result=test_result,
            worktree_path=worktree_path,
        )
        self._session.add(row)
        self._session.commit()

    def _notify_agent_failure(self, role_name: str, error: Exception) -> None:
        logger.error("Implementation Agent %s failed after retries: %s", role_name, error)

    def _execute_agent(
        self, agent: ImplementationAgent, design_doc: dict,
        workspace: Workspace | None = None,
    ) -> CodeOutput | None:
        return retry_with_backoff(
            lambda: agent.generate(design_doc, self._adapter, workspace),
            max_retries=self.MAX_RETRIES,
            on_exhausted=lambda e: self._notify_agent_failure(agent.role_name, e),
        )

    @staticmethod
    def _aggregate_results(req_id: str, outputs: list[CodeOutput]) -> CodeResult:
        merged_files: dict[str, str] = {}
        all_notes: list[str] = []

        for output in outputs:
            for file in output.code_files:
                merged_files[file["path"]] = file["content"]
            all_notes.extend(output.ambiguity_notes)

        code_files = [{"path": k, "content": v} for k, v in merged_files.items()]

        return CodeResult(
            requirement_id=req_id,
            code_files=code_files,
            ambiguity_notes=all_notes,
        )

    def run_implementation(self, req_id: str) -> CodeResult:
        design_doc = self._load_design_output(req_id)

        ws: Workspace | None = None
        if self._adapter is not None or self._wm is not None:
            wm = self._wm or WorkspaceManager()
            ws = wm.acquire_workspace(req_id, "implementation")

        results: list[CodeOutput] = []

        with ThreadPoolExecutor(max_workers=len(self._agents)) as executor:
            future_to_agent = {
                executor.submit(self._execute_agent, agent, design_doc, ws): agent
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
                    results.append(result)

        if not results:
            if ws is not None:
                wm = self._wm or WorkspaceManager()
                wm.release_workspace(req_id, "implementation")
            raise AllAgentsFailedError(req_id)

        code_result = self._aggregate_results(req_id, results)

        test_result: TestResult | None = None
        if ws is not None and self._test_runner is not None:
            test_result = self._test_runner.run_tests(ws)
            code_result.test_result = test_result.model_dump()
            code_result.worktree_path = ws.path

        if ws is not None:
            wm = self._wm or WorkspaceManager()
            wm.release_workspace(req_id, "implementation")

        self._persist_output(req_id, code_result.code_files,
                             test_result=code_result.test_result,
                             worktree_path=code_result.worktree_path)
        return code_result
