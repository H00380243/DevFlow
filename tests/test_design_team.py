"""Tests for DesignTeam & DesignAgent — F012 设计团多角色产出."""

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
def requirement(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260708-001",
        original_text="实现用户行为分析系统",
        summary="用户行为分析系统",
        submitter_id="user001",
        current_stage="design",
        current_status="IN_DESIGN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


@pytest.fixture
def structured_requirement() -> StructuredRequirement:
    return StructuredRequirement(
        id="REQ-20260708-001",
        original_text="实现用户行为分析系统",
        summary="用户行为分析系统",
        submitter_id="user001",
    )


# ----- DesignAgent Tests -----


class TestDesignAgentProductDesignHappy:
    """T001: FUNC/happy — 产品设计 agent returns valid design output."""

    def test_product_design_output(self, structured_requirement):
        from app.core.design_team import DesignAgent, DesignOutput

        agent = DesignAgent(role_name="产品设计")
        mock_response = json.dumps({
            "document_content": "用户行为分析系统概要设计",
            "user_flow": "用户登录→行为采集→分析展示",
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.design(structured_requirement)

        assert isinstance(result, DesignOutput)
        assert result.agent_role == "产品设计"
        assert result.document_content == "用户行为分析系统概要设计"
        assert result.user_flow == "用户登录→行为采集→分析展示"


class TestDesignAgentTechSelectionHappy:
    """T001: FUNC/happy — 技术选型 agent returns skeleton_dirs and core_interfaces."""

    def test_tech_selection_output(self, structured_requirement):
        from app.core.design_team import DesignAgent, DesignOutput

        agent = DesignAgent(role_name="技术选型")
        mock_response = json.dumps({
            "skeleton_dirs": ["src/collector", "src/analyzer", "src/reporter"],
            "core_interfaces": [
                {"module": "collector", "method": "collect_event", "signature": "def collect_event(user_id: str) -> dict"},
            ],
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.design(structured_requirement)

        assert isinstance(result, DesignOutput)
        assert result.agent_role == "技术选型"
        assert len(result.skeleton_dirs) == 3
        assert result.skeleton_dirs[0] == "src/collector"
        assert len(result.core_interfaces) == 1


class TestDesignAgentComplianceRiskHappy:
    """T002: FUNC/happy — 合规风控 agent returns risk_warnings with high risk."""

    def test_compliance_high_risk(self, structured_requirement):
        from app.core.design_team import DesignAgent, DesignOutput

        agent = DesignAgent(role_name="合规风控")
        mock_response = json.dumps({
            "risk_warnings": ["涉及用户隐私数据(PII)"],
            "recommendations": "需要数据脱敏处理",
            "has_high_risk": True,
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.design(structured_requirement)

        assert isinstance(result, DesignOutput)
        assert result.agent_role == "合规风控"
        assert len(result.risk_warnings) == 1
        assert result.risk_warnings[0] == "涉及用户隐私数据(PII)"
        assert result.has_high_risk is True
        assert result.recommendations == "需要数据脱敏处理"


class TestDesignAgentLowRisk:
    """T002 variation: 合规风控 with no high risk — no [高风险] annotation."""

    def test_compliance_low_risk(self, structured_requirement):
        from app.core.design_team import DesignAgent, DesignOutput

        agent = DesignAgent(role_name="合规风控")
        mock_response = json.dumps({
            "risk_warnings": ["建议增加审计日志"],
            "recommendations": "",
            "has_high_risk": False,
        })
        agent.call_llm = MagicMock(return_value=mock_response)

        result = agent.design(structured_requirement)

        assert result.has_high_risk is False
        assert result.risk_warnings[0] == "建议增加审计日志"


class TestDesignAgentParseErrorNonJson:
    """T008: BNDRY/edge — non-JSON LLM response raises DesignParseError."""

    def test_non_json_response(self, structured_requirement):
        from app.core.design_team import DesignAgent, DesignParseError

        agent = DesignAgent(role_name="产品设计")
        agent.call_llm = MagicMock(return_value="not json at all")

        with pytest.raises(DesignParseError) as excinfo:
            agent.design(structured_requirement)

        assert "产品设计" in str(excinfo.value)


class TestDesignAgentMissingFields:
    """T005: BNDRY/edge — empty JSON response raises DesignParseError."""

    def test_missing_fields(self, structured_requirement):
        from app.core.design_team import DesignAgent, DesignParseError

        agent = DesignAgent(role_name="产品设计")
        agent.call_llm = MagicMock(return_value=json.dumps({}))

        with pytest.raises(DesignParseError):
            agent.design(structured_requirement)


class TestDesignAgentPromptConstruction:
    """Prompt contains role name and requirement info."""

    def test_prompt_contains_role_and_requirement(self, structured_requirement):
        from app.core.design_team import DesignAgent

        agent = DesignAgent(role_name="技术选型")
        agent.call_llm = MagicMock(return_value=json.dumps({
            "skeleton_dirs": [],
            "core_interfaces": [],
        }))

        agent.design(structured_requirement)

        actual_prompt = agent.call_llm.call_args[0][0]
        assert "技术选型" in actual_prompt
        assert "REQ-20260708-001" in actual_prompt
        assert "用户行为分析系统" in actual_prompt


# ----- DesignTeam Tests -----


class TestDesignTeamRunDesignHappy:
    """T001: FUNC/happy — all 3 agents succeed, DesignResult returned with all fields."""

    def test_all_agents_succeed(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignResult, DesignTeam

        team = DesignTeam(db_session)

        product_json = json.dumps({"document_content": "概要设计", "user_flow": "flow"})
        tech_json = json.dumps({
            "skeleton_dirs": ["src/a"],
            "core_interfaces": [{"module": "a", "method": "fn"}],
        })
        compliance_json = json.dumps({"risk_warnings": ["风险"], "has_high_risk": False})

        responses = [product_json, tech_json, compliance_json]
        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=responses[team._agents.index(agent)])

        result = team.run_design("REQ-20260708-001")

        assert isinstance(result, DesignResult)
        assert result.requirement_id == "REQ-20260708-001"
        assert result.document_url is not None
        assert len(result.skeleton_dirs) == 1
        assert len(result.core_interfaces) == 1
        assert result.version == 1

        rows = db_session.query(DesignResults).filter(
            DesignResults.requirement_id == "REQ-20260708-001"
        ).all()
        assert len(rows) == 3


class TestDesignTeamRunDesignHighRisk:
    """T002: FUNC/happy — 合规风控 high risk annotated with [高风险] prefix."""

    def test_high_risk_annotated(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)

        product_json = json.dumps({"document_content": "doc", "user_flow": ""})
        tech_json = json.dumps({"skeleton_dirs": [], "core_interfaces": []})
        compliance_json = json.dumps({
            "risk_warnings": ["涉及PII数据"],
            "has_high_risk": True,
        })

        responses = [product_json, tech_json, compliance_json]
        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=responses[team._agents.index(agent)])

        result = team.run_design("REQ-20260708-001")

        assert len(result.risk_warnings) == 1
        assert result.risk_warnings[0].startswith("[高风险]")


class TestDesignTeamAllAgentsFail:
    """T003: FUNC/error — all 3 agents fail, raises AllAgentsFailedError."""

    def test_all_agents_fail(self, db_session, requirement, structured_requirement):
        from app.core.design_team import AllAgentsFailedError, DesignTeam

        team = DesignTeam(db_session)
        for agent in team._agents:
            agent.call_llm = MagicMock(side_effect=ConnectionError("LLM down"))
        team._notify_agent_failure = MagicMock()

        import app.core.design_team as dt
        original_sleep = dt.time.sleep
        dt.time.sleep = MagicMock()

        try:
            with pytest.raises(AllAgentsFailedError) as excinfo:
                team.run_design("REQ-20260708-001")
            assert "REQ-20260708-001" in str(excinfo.value)
            assert team._notify_agent_failure.call_count == 3
        finally:
            dt.time.sleep = original_sleep


class TestDesignTeamRetryThenSuccess:
    """T004: FUNC/retry — agent fails 2x then succeeds on 3rd attempt."""

    def test_retry_then_success(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)
        agent = team._agents[0]

        success_json = json.dumps({"document_content": "doc", "user_flow": ""})
        call_count = 0

        def flaky_call_llm(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("LLM timeout")
            return success_json

        agent.call_llm = flaky_call_llm
        team._notify_agent_failure = MagicMock()

        import app.core.design_team as dt
        original_sleep = dt.time.sleep
        dt.time.sleep = MagicMock()

        try:
            result = team._execute_agent(agent, structured_requirement)
            assert result is not None
            assert result.agent_role == "产品设计"
            assert call_count == 3
            team._notify_agent_failure.assert_not_called()
        finally:
            dt.time.sleep = original_sleep


class TestDesignTeamPartialResult:
    """T006: BNDRY/edge — only 1 agent succeeds, partial result returned."""

    def test_partial_result(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)

        product_json = json.dumps({"document_content": "概要设计", "user_flow": ""})
        for i, agent in enumerate(team._agents):
            if i == 0:
                agent.call_llm = MagicMock(return_value=product_json)
            else:
                agent.call_llm = MagicMock(side_effect=ConnectionError("down"))

        team._notify_agent_failure = MagicMock()

        import app.core.design_team as dt
        original_sleep = dt.time.sleep
        dt.time.sleep = MagicMock()

        try:
            result = team.run_design("REQ-20260708-001")
            assert result.document_url is not None
        finally:
            dt.time.sleep = original_sleep


class TestDesignTeamRequirementNotFound:
    """T007: FUNC/error — missing req_id raises RequirementNotFoundError."""

    def test_requirement_not_found(self, db_session):
        from app.core.state_machine import RequirementNotFoundError
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)

        with pytest.raises(RequirementNotFoundError):
            team.run_design("REQ-NONEXIST-001")


class TestDesignTeamEmptyOutput:
    """T005: BNDRY/edge — 技术选型 returns empty lists."""

    def test_empty_tech_output(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)

        product_json = json.dumps({"document_content": "doc", "user_flow": ""})
        tech_json = json.dumps({"skeleton_dirs": [], "core_interfaces": []})
        compliance_json = json.dumps({"risk_warnings": [], "has_high_risk": False})

        responses = [product_json, tech_json, compliance_json]
        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=responses[team._agents.index(agent)])

        result = team.run_design("REQ-20260708-001")

        assert result.skeleton_dirs == []
        assert result.core_interfaces == []


class TestDesignTeamVersionFirst:
    """T009: BNDRY/edge — first design version is 1."""

    def test_first_design_version(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)
        product_json = json.dumps({"document_content": "doc", "user_flow": ""})
        tech_json = json.dumps({"skeleton_dirs": [], "core_interfaces": []})
        compliance_json = json.dumps({"risk_warnings": [], "has_high_risk": False})

        responses = [product_json, tech_json, compliance_json]
        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=responses[team._agents.index(agent)])

        result = team.run_design("REQ-20260708-001")
        assert result.version == 1


class TestDesignTeamVersionRedesign:
    """T010: BNDRY/edge — re-design increments version."""

    def test_redesign_increments_version(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)
        product_json = json.dumps({"document_content": "doc", "user_flow": ""})
        tech_json = json.dumps({"skeleton_dirs": [], "core_interfaces": []})
        compliance_json = json.dumps({"risk_warnings": [], "has_high_risk": False})

        responses = [product_json, tech_json, compliance_json]
        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=responses[team._agents.index(agent)])

        result1 = team.run_design("REQ-20260708-001")
        assert result1.version == 1

        result2 = team.run_design("REQ-20260708-001")
        assert result2.version == 2


class TestDesignTeamExponentialBackoff:
    """PERF — verify exponential backoff timing on retry."""

    def test_exponential_backoff_timing(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)
        agent = team._agents[0]
        success_json = json.dumps({"document_content": "doc", "user_flow": ""})
        call_count = 0

        def flaky_call_llm(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("bad parse")
            return success_json

        agent.call_llm = flaky_call_llm
        team._notify_agent_failure = MagicMock()

        time_sleeps = []

        def mock_sleep(seconds):
            time_sleeps.append(seconds)

        import app.core.design_team as dt
        original_sleep = dt.time.sleep
        dt.time.sleep = mock_sleep

        try:
            result = team._execute_agent(agent, structured_requirement)
            assert result is not None
            assert len(time_sleeps) == 2
            assert time_sleeps[0] == pytest.approx(1.0, abs=0.5)
            assert time_sleeps[1] == pytest.approx(2.0, abs=0.5)
        finally:
            dt.time.sleep = original_sleep


class TestDesignTeamParallelExecution:
    """T011: PERF/parallel — verify parallel execution (3 agents < 1.5s serial)."""

    def test_parallel_execution(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)
        responses = [
            json.dumps({"document_content": "doc", "user_flow": ""}),
            json.dumps({"skeleton_dirs": [], "core_interfaces": []}),
            json.dumps({"risk_warnings": [], "has_high_risk": False}),
        ]

        for idx, agent in enumerate(team._agents):
            agent.call_llm = lambda prompt, idx=idx, delay=0.5: (
                time.sleep(delay) or responses[idx]
            )

        start = time.time()
        result = team.run_design("REQ-20260708-001")
        elapsed = time.time() - start
        assert elapsed < 1.5
        assert result.document_url is not None


class TestDesignTeamDbFailure:
    """T013: FUNC/error — DB write failure propagates exception."""

    def test_db_write_failure(self, db_session, requirement, structured_requirement):
        from app.core.design_team import DesignTeam

        team = DesignTeam(db_session)
        product_json = json.dumps({"document_content": "doc", "user_flow": ""})
        tech_json = json.dumps({"skeleton_dirs": [], "core_interfaces": []})
        compliance_json = json.dumps({"risk_warnings": [], "has_high_risk": False})

        responses = [product_json, tech_json, compliance_json]
        for agent in team._agents:
            agent.call_llm = MagicMock(return_value=responses[team._agents.index(agent)])

        team._session.add = MagicMock(side_effect=RuntimeError("DB write failed"))

        with pytest.raises(RuntimeError, match="DB write failed"):
            team.run_design("REQ-20260708-001")
