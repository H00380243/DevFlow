"""Tests for ImplementationTeam & ImplementationAgent — F015 实施团代码生成."""

import json
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Base,
    DesignResults,
    ImplementationResults,
    Requirements,
    StructuredRequirement,
)


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
def requirement_with_design(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260708-001",
        original_text="实现用户行为分析系统",
        summary="用户行为分析系统",
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
            document_url="design://REQ-20260708-001/v1",
            skeleton_dirs=["src/collector", "src/analyzer"] if role == "技术选型" else None,
            core_interfaces=[
                {"module": "collector", "method": "collect_event"}
            ] if role == "技术选型" else None,
            risk_warnings=["涉及用户隐私"] if role == "合规风控" else None,
            created_at=datetime.now(timezone.utc),
            version=1,
        )
        db_session.add(dr)

    db_session.commit()
    return req


@pytest.fixture
def requirement_in_design_state(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260708-002",
        original_text="简单需求",
        summary="",
        submitter_id="user002",
        current_stage="design",
        current_status="IN_DESIGN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


@pytest.fixture
def design_doc() -> dict:
    return {
        "requirement_id": "REQ-20260708-001",
        "original_text": "实现用户行为分析系统",
        "summary": "用户行为分析系统",
        "design_content": "概要设计文档内容",
        "skeleton_dirs": ["src/collector", "src/analyzer"],
        "core_interfaces": [{"module": "collector", "method": "collect_event"}],
        "risk_warnings": ["涉及用户隐私"],
        "version": 1,
    }


# ----- ImplementationAgent Tests -----


class TestImplementationAgentBackendHappy:
    """T001: FUNC/happy — 后端开发 agent returns valid code files."""

    def test_backend_agent_output(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeOutput

        agent = ImplementationAgent(role_name="后端开发")
        mock_response = json.dumps({
            "code_files": [
                {"path": "src/collector/event_collector.py", "content": "def collect(): pass"},
            ],
            "ambiguity_notes": [],
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.generate(design_doc)

        assert isinstance(result, CodeOutput)
        assert result.agent_role == "后端开发"
        assert len(result.code_files) == 1
        assert result.code_files[0]["path"] == "src/collector/event_collector.py"
        assert result.code_files[0]["content"] == "def collect(): pass"


class TestImplementationAgentFrontendHappy:
    """T001: FUNC/happy — 前端开发 agent returns valid code files."""

    def test_frontend_agent_output(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeOutput

        agent = ImplementationAgent(role_name="前端开发")
        mock_response = json.dumps({
            "code_files": [
                {"path": "frontend/pages/analysis.py", "content": "def render(): pass"},
            ],
            "ambiguity_notes": [],
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.generate(design_doc)

        assert isinstance(result, CodeOutput)
        assert result.agent_role == "前端开发"


class TestImplementationAgentQAWithAmbiguity:
    """T002: FUNC/happy — 质量保障 agent returns ambiguity notes when design is ambiguous."""

    def test_ambiguity_annotation(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeOutput

        agent = ImplementationAgent(role_name="质量保障")
        mock_response = json.dumps({
            "code_files": [
                {"path": "tests/test_collector.py", "content": "def test_collect(): pass"},
            ],
            "ambiguity_notes": [
                "设计未明确事件采集频率，按默认实时采集实现",
            ],
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.generate(design_doc)

        assert len(result.ambiguity_notes) == 1
        assert "事件采集频率" in result.ambiguity_notes[0]


class TestImplementationAgentParseErrorNonJson:
    """T008: BNDRY/edge — non-JSON LLM response raises CodeParseError."""

    def test_non_json_response(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeParseError

        agent = ImplementationAgent(role_name="后端开发")
        agent.call_llm = MagicMock(return_value="not json at all")

        with pytest.raises(CodeParseError) as excinfo:
            agent.generate(design_doc)

        assert "后端开发" in str(excinfo.value)


class TestImplementationAgentMissingCodeFiles:
    """T005: BNDRY/edge — LLM response missing code_files key raises CodeParseError."""

    def test_missing_code_files(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeParseError

        agent = ImplementationAgent(role_name="前端开发")
        mock_response = json.dumps({"ambiguity_notes": []})
        agent.call_llm = MagicMock(return_value=mock_response)

        with pytest.raises(CodeParseError):
            agent.generate(design_doc)


class TestImplementationAgentFileFieldsMalformed:
    """T005: BNDRY/edge — code_files entry missing path/content raises CodeParseError."""

    def test_malformed_file_entry(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeParseError

        agent = ImplementationAgent(role_name="后端开发")
        mock_response = json.dumps({
            "code_files": [{"path": "only_path.txt"}],
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        with pytest.raises(CodeParseError):
            agent.generate(design_doc)


class TestImplementationAgentRetryThenSuccess:
    """T004: FUNC/retry — agent fails twice, succeeds on 3rd attempt."""

    def test_retry_then_success(self, design_doc):
        from app.core.implementation_team import ImplementationAgent, CodeOutput

        agent = ImplementationAgent(role_name="后端开发")
        call_count = 0

        def flaky_call(_prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("LLM temporarily unavailable")
            return json.dumps({
                "code_files": [{"path": "src/main.py", "content": "def main(): pass"}],
                "ambiguity_notes": [],
            })

        agent.call_llm = flaky_call

        from app.core.implementation_team import retry_with_backoff
        result = retry_with_backoff(
            lambda: agent.generate(design_doc),
            max_retries=3,
        )

        assert isinstance(result, CodeOutput)
        assert call_count == 3


# ----- ImplementationTeam Tests -----


class TestImplementationTeamFullSuccess:
    """T001: FUNC/happy — all 3 agents succeed, code files aggregated and persisted."""

    def test_full_success(self, requirement_with_design, db_session, design_doc):
        from app.core.implementation_team import ImplementationTeam

        team = ImplementationTeam(session=db_session)
        team._load_design_output = MagicMock(return_value=design_doc)

        backend_output = {
            "code_files": [{"path": "src/backend.py", "content": "def process(): pass"}],
            "ambiguity_notes": [],
        }
        frontend_output = {
            "code_files": [{"path": "frontend/ui.py", "content": "def render(): pass"}],
            "ambiguity_notes": [],
        }
        qa_output = {
            "code_files": [{"path": "tests/test_main.py", "content": "def test(): pass"}],
            "ambiguity_notes": ["设计未明确日志格式"],
        }

        def mock_generate(role, doc):
            from app.core.implementation_team import CodeOutput
            if role == "后端开发":
                d = backend_output
            elif role == "前端开发":
                d = frontend_output
            else:
                d = qa_output
            return CodeOutput(
                agent_role=role,
                raw_text=json.dumps(d),
                code_files=d["code_files"],
                ambiguity_notes=d["ambiguity_notes"],
            )

        original = team._execute_agent

        def _execute_side_effect(agent, doc):
            return mock_generate(agent.role_name, doc)

        team._execute_agent = _execute_side_effect

        result = team.run_implementation("REQ-20260708-001")

        assert result.requirement_id == "REQ-20260708-001"
        assert len(result.code_files) == 3
        assert len(result.ambiguity_notes) == 1

        row = db_session.query(ImplementationResults).filter(
            ImplementationResults.requirement_id == "REQ-20260708-001"
        ).first()
        assert row is not None
        assert len(row.code_files) == 3


class TestImplementationTeamDedupByPath:
    """T001: FUNC/happy — code files deduplicated by path (last writer wins)."""

    def test_dedup(self, requirement_with_design, db_session, design_doc):
        from app.core.implementation_team import ImplementationTeam, CodeOutput

        team = ImplementationTeam(session=db_session)
        team._load_design_output = MagicMock(return_value=design_doc)

        def _execute_side_effect(agent, doc):
            return CodeOutput(
                agent_role=agent.role_name,
                raw_text="mock raw",
                code_files=[{"path": "shared.py", "content": f"# {agent.role_name} version"}],
                ambiguity_notes=[],
            )

        team._execute_agent = _execute_side_effect

        result = team.run_implementation("REQ-20260708-001")

        assert len(result.code_files) == 1
        assert result.code_files[0]["path"] == "shared.py"
        assert result.code_files[0]["content"] in (
            "# 后端开发 version", "# 前端开发 version", "# 质量保障 version",
        )


class TestImplementationTeamPartialSuccess:
    """T009: BNDRY/edge — only 1 agent succeeds, 2 fail after retries."""

    def test_partial_success(self, requirement_with_design, db_session, design_doc):
        from app.core.implementation_team import ImplementationTeam, CodeOutput

        team = ImplementationTeam(session=db_session)
        team._load_design_output = MagicMock(return_value=design_doc)

        call_count = {"backend": 0}

        def _execute_side_effect(agent, doc):
            if agent.role_name == "后端开发":
                return CodeOutput(
                    agent_role="后端开发",
                    raw_text="mock raw",
                    code_files=[{"path": "src/main.py", "content": "def main(): pass"}],
                    ambiguity_notes=[],
                )
            return None

        team._execute_agent = _execute_side_effect

        result = team.run_implementation("REQ-20260708-001")

        assert len(result.code_files) == 1
        assert result.code_files[0]["path"] == "src/main.py"

        row = db_session.query(ImplementationResults).filter(
            ImplementationResults.requirement_id == "REQ-20260708-001"
        ).first()
        assert row is not None


class TestImplementationTeamAllAgentsFail:
    """T003/T011: FUNC/error — all 3 agents return None after retries → AllAgentsFailedError."""

    def test_all_agents_fail(self, requirement_with_design, db_session, design_doc):
        from app.core.implementation_team import ImplementationTeam, AllAgentsFailedError

        team = ImplementationTeam(session=db_session)
        team._load_design_output = MagicMock(return_value=design_doc)

        team._execute_agent = MagicMock(return_value=None)

        with pytest.raises(AllAgentsFailedError) as excinfo:
            team.run_implementation("REQ-20260708-001")

        assert "REQ-20260708-001" in str(excinfo.value)


class TestImplementationTeamEmptyCodeFiles:
    """T005: BNDRY/edge — all agents return empty code_files list."""

    def test_empty_code_files(self, requirement_with_design, db_session, design_doc):
        from app.core.implementation_team import ImplementationTeam, CodeOutput

        team = ImplementationTeam(session=db_session)
        team._load_design_output = MagicMock(return_value=design_doc)

        def _execute_side_effect(agent, doc):
            return CodeOutput(
                agent_role=agent.role_name,
                raw_text="mock raw",
                code_files=[],
                ambiguity_notes=[],
            )

        team._execute_agent = _execute_side_effect

        result = team.run_implementation("REQ-20260708-001")

        assert len(result.code_files) == 0
        row = db_session.query(ImplementationResults).filter(
            ImplementationResults.requirement_id == "REQ-20260708-001"
        ).first()
        assert row is not None
        assert row.code_files == []


class TestImplementationTeamMissingDesign:
    """T006: FUNC/error — req_id has no design outputs."""

    def test_no_design_outputs(self, requirement_in_design_state, db_session):
        from app.core.implementation_team import ImplementationTeam
        from app.core.state_machine import RequirementNotFoundError

        team = ImplementationTeam(session=db_session)

        with pytest.raises(RequirementNotFoundError) as excinfo:
            team.run_implementation("REQ-20260708-002")

        assert "design" in str(excinfo.value).lower()


class TestImplementationTeamMissingRequirement:
    """T007: FUNC/error — req_id not found in DB."""

    def test_missing_requirement(self, db_session):
        from app.core.implementation_team import ImplementationTeam
        from app.core.state_machine import RequirementNotFoundError

        team = ImplementationTeam(session=db_session)

        with pytest.raises(RequirementNotFoundError):
            team.run_implementation("NONEXISTENT")


class TestImplementationTeamParallelExecution:
    """T012: PERF/parallel — agents run in parallel, not serial."""

    def test_parallel_execution(self, requirement_with_design, db_session, design_doc):
        from app.core.implementation_team import ImplementationTeam, CodeOutput

        team = ImplementationTeam(session=db_session)
        team._load_design_output = MagicMock(return_value=design_doc)

        def _execute_side_effect(agent, doc):
            time.sleep(0.3)
            return CodeOutput(
                agent_role=agent.role_name,
                raw_text="mock raw",
                code_files=[{"path": f"{agent.role_name}.py", "content": "pass"}],
                ambiguity_notes=[],
            )

        team._execute_agent = _execute_side_effect

        start = time.time()
        result = team.run_implementation("REQ-20260708-001")
        elapsed = time.time() - start

        assert len(result.code_files) == 3
        assert elapsed < 0.9


class TestImplementationTeamRealLoadDesignOutput:
    """INTG: Uses real _load_design_output (not mocked) — covers full stack."""

    def test_full_flow_real_load(self, requirement_with_design, db_session):
        from app.core.implementation_team import ImplementationTeam, CodeOutput, CodeResult

        team = ImplementationTeam(session=db_session)

        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=json.dumps({
                "code_files": [{"path": f"src/{agent.role_name}.py", "content": "# code"}],
                "ambiguity_notes": [],
            }))

        result = team.run_implementation("REQ-20260708-001")

        assert isinstance(result, CodeResult)
        assert result.requirement_id == "REQ-20260708-001"
        assert len(result.code_files) == 3

        row = db_session.query(ImplementationResults).filter(
            ImplementationResults.requirement_id == "REQ-20260708-001"
        ).first()
        assert row is not None
        assert len(row.code_files) == 3

    def test_real_load_agent_retry_then_succeed(self, requirement_with_design, db_session):
        from app.core.implementation_team import ImplementationTeam, CodeResult

        team = ImplementationTeam(session=db_session)

        call_count = {"后端开发": 0}

        def flaky_call(role):
            def fn(_prompt):
                nonlocal call_count
                call_count[role] += 1
                if call_count[role] < 3:
                    raise RuntimeError("LLM unavailable")
                return json.dumps({
                    "code_files": [{"path": f"src/{role}.py", "content": "# done"}],
                    "ambiguity_notes": [],
                })
            return fn

        for agent in team._agents:
            if agent.role_name == "后端开发":
                agent.call_llm = flaky_call("后端开发")
            else:
                agent.call_llm = MagicMock(return_value=json.dumps({
                    "code_files": [{"path": f"src/{agent.role_name}.py", "content": "# code"}],
                    "ambiguity_notes": [],
                }))

        result = team.run_implementation("REQ-20260708-001")

        assert isinstance(result, CodeResult)
        assert call_count["后端开发"] == 3
        assert len(result.code_files) == 3
