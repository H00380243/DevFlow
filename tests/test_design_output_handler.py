"""Tests for DesignOutputHandler — F013 设计产出物生成."""

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
def requirement_in_design(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260708-001",
        original_text="实现用户行为分析系统，支持analyze事件收集",
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
def requirement_rejected(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260708-002",
        original_text="测试需求",
        summary="测试",
        submitter_id="user002",
        current_stage="review",
        current_status="REJECTED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


@pytest.fixture
def design_outputs(db_session, requirement_in_design) -> list[DesignResults]:
    now = datetime.now(timezone.utc)
    outputs = [
        DesignResults(
            requirement_id="REQ-20260708-001",
            agent_role="产品设计",
            document_url="用户行为分析系统概要设计：实现事件采集、存储、分析",
            skeleton_dirs=None,
            core_interfaces=None,
            risk_warnings=None,
            created_at=now,
            version=1,
        ),
        DesignResults(
            requirement_id="REQ-20260708-001",
            agent_role="技术选型",
            document_url="",
            skeleton_dirs=["src/collector", "src/analyzer"],
            core_interfaces=[
                {"module": "collector", "method": "collect_event", "signature": "def collect_event(user_id: str) -> dict"},
                {"module": "analyzer", "method": "analyze", "signature": "def analyze(data: list) -> dict"},
            ],
            risk_warnings=None,
            created_at=now,
            version=1,
        ),
        DesignResults(
            requirement_id="REQ-20260708-001",
            agent_role="合规风控",
            document_url="",
            skeleton_dirs=None,
            core_interfaces=None,
            risk_warnings=["涉及用户隐私数据"],
            created_at=now,
            version=1,
        ),
    ]
    for o in outputs:
        db_session.add(o)
    db_session.commit()
    return outputs


@pytest.fixture
def mock_upload_fn():
    return MagicMock(return_value="http://minio/design/REQ-20260708-001/v1.json")


@pytest.fixture
def mock_push_fn():
    return MagicMock()


@pytest.fixture
def handler(db_session, mock_upload_fn, mock_push_fn):
    from app.core.design_output_handler import DesignOutputHandler
    return DesignOutputHandler(
        session=db_session,
        upload_fn=mock_upload_fn,
        push_fn=mock_push_fn,
    )


# ----- Complete Design Tests -----


class TestCompleteDesignHappy:
    """T01: FUNC/happy — complete_design full flow."""

    def test_complete_design_returns_url(self, handler, design_outputs, mock_upload_fn, mock_push_fn):
        from app.core.state_machine import Status

        url = handler.complete_design("REQ-20260708-001")

        assert url == "http://minio/design/REQ-20260708-001/v1.json"
        mock_upload_fn.assert_called_once()
        assert "REQ-20260708-001" in mock_upload_fn.call_args[0][1]

        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.DESIGN_PENDING_CONFIRM

        mock_push_fn.assert_called_once()
        assert "REQ-20260708-001" in mock_push_fn.call_args[0][1]


class TestCompleteDesignUploadFailure:
    """T03: FUNC/error — upload fails 3 times, admin notified, state unchanged."""

    def test_upload_failure_notifies_admin(self, handler, design_outputs, mock_upload_fn, mock_push_fn):
        from app.core.design_output_handler import UploadFailedError
        from app.core.state_machine import Status

        mock_upload_fn.side_effect = ConnectionError("MinIO not reachable")

        with pytest.raises(UploadFailedError) as excinfo:
            handler.complete_design("REQ-20260708-001")

        assert "REQ-20260708-001" in str(excinfo.value) or "v1.json" in str(excinfo.value)
        assert mock_upload_fn.call_count == 3

        admin_call = [c for c in mock_push_fn.call_args_list if "admin" in c[0][0] or "上传失败" in c[0][1]]
        assert len(admin_call) >= 1

        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.IN_DESIGN


class TestCompleteDesignRequirementNotFound:
    """T04: FUNC/error — non-existent req_id."""

    def test_requirement_not_found(self, handler):
        from app.core.state_machine import RequirementNotFoundError

        with pytest.raises(RequirementNotFoundError):
            handler.complete_design("REQ-NONEXIST-001")


class TestCompleteDesignNoDesignOutputs:
    """T06: FUNC/error — no DesignResults rows exist."""

    def test_no_design_outputs(self, handler, requirement_in_design):
        from app.core.state_machine import RequirementNotFoundError

        with pytest.raises(RequirementNotFoundError):
            handler.complete_design("REQ-20260708-001")


class TestCompleteDesignStateTransition:
    """T12: FUNC/state — verify state transition after success."""

    def test_state_transition(self, handler, design_outputs):
        from app.core.state_machine import Status

        url = handler.complete_design("REQ-20260708-001")
        assert url

        status = handler._sm.get_status("REQ-20260708-001")
        assert status == Status.DESIGN_PENDING_CONFIRM


# ----- Upload Document Tests -----


class TestUploadDocumentEmptyContent:
    """T07: FUNC/error — empty content raises UploadFailedError."""

    def test_empty_content_raises(self, handler):
        from app.core.design_output_handler import UploadFailedError

        with pytest.raises(UploadFailedError) as excinfo:
            handler.upload_document("", "test/path.json")

        assert "empty" in str(excinfo.value).lower()


class TestUploadDocumentEmptyFilename:
    """T07 extension: empty filename raises UploadFailedError."""

    def test_empty_filename_raises(self, handler):
        from app.core.design_output_handler import UploadFailedError

        with pytest.raises(UploadFailedError) as excinfo:
            handler.upload_document("content", "")

        assert "empty" in str(excinfo.value).lower()


class TestUploadDocumentRetrySuccess:
    """T11: BNDRY/edge — upload fails once then succeeds."""

    def test_retry_then_succeeds(self, handler, mock_upload_fn):
        mock_upload_fn.side_effect = [ConnectionError("timeout"), "http://minio/doc.json"]
        handler._upload_fn = mock_upload_fn

        import app.core.design_output_handler as doh
        original_sleep = doh.time.sleep
        doh.time.sleep = MagicMock()

        try:
            url = handler.upload_document("content", "test/path.json")
            assert url == "http://minio/doc.json"
            assert mock_upload_fn.call_count == 2
        finally:
            doh.time.sleep = original_sleep


class TestUploadDocumentExhaustedRetries:
    """T03: FUNC/error extension — all retries exhausted."""

    def test_all_retries_exhausted(self, handler, mock_upload_fn):
        from app.core.design_output_handler import UploadFailedError

        mock_upload_fn.side_effect = ConnectionError("down")
        handler._upload_fn = mock_upload_fn

        import app.core.design_output_handler as doh
        original_sleep = doh.time.sleep
        doh.time.sleep = MagicMock()

        try:
            with pytest.raises(UploadFailedError):
                handler.upload_document("content", "test/path.json")
            assert mock_upload_fn.call_count == 3
        finally:
            doh.time.sleep = original_sleep


# ----- Validate Interfaces Tests -----


class TestValidateInterfacesHappy:
    """T02: FUNC/happy — correct interface marking."""

    def test_validate_interfaces(self, handler):
        interfaces = [
            {"module": "c", "method": "collect_event", "signature": "def collect_event()"},
            {"module": "r", "method": "unknown_fn", "signature": "def unknown_fn()"},
            {"module": "e", "method": "analyze", "signature": ""},
        ]
        req_text = "实现用户行为分析系统，支持analyze事件收集"

        result = handler._validate_interfaces(interfaces, req_text)

        assert len(result) == 3
        assert result[0]["is_confirmed"] is False  # collect_event not in text
        assert result[1]["is_confirmed"] is False  # unknown_fn not in text
        assert result[2]["is_confirmed"] is False  # signature empty


class TestValidateInterfacesEmpty:
    """T08: BNDRY/edge — empty interfaces list."""

    def test_empty_interfaces(self, handler):
        result = handler._validate_interfaces([], "some text")
        assert result == []


class TestValidateInterfacesMethodNotInText:
    """T09: BNDRY/edge — method not in requirement text."""

    def test_method_not_in_text(self, handler):
        interfaces = [{"method": "send_email", "signature": "def send_email()"}]
        result = handler._validate_interfaces(interfaces, "用户行为分析")
        assert result[0]["is_confirmed"] is False


class TestValidateInterfacesMethodInText:
    """T10: BNDRY/edge — method name substring found in text."""

    def test_method_in_text(self, handler):
        interfaces = [{"method": "analyze", "signature": "def analyze()"}]
        result = handler._validate_interfaces(interfaces, "用户行为analyze系统")
        assert result[0]["is_confirmed"] is True


class TestValidateInterfacesMissingKeys:
    """Edge case: dict missing method/signature keys."""

    def test_missing_keys(self, handler):
        interfaces = [{"module": "x"}]
        result = handler._validate_interfaces(interfaces, "text")
        assert result[0]["is_confirmed"] is False


# ----- Generate Document Tests -----


class TestGenerateDocumentHappy:
    """T01 extension — verify generated document structure."""

    def test_generated_document_structure(self, handler, design_outputs):
        doc_str = handler._generate_document(
            "REQ-20260708-001", 1, design_outputs
        )
        doc = json.loads(doc_str)

        assert doc["requirement_id"] == "REQ-20260708-001"
        assert doc["version"] == 1
        assert doc["design_content"] == "用户行为分析系统概要设计：实现事件采集、存储、分析"
        assert len(doc["skeleton_dirs"]) == 2
        assert len(doc["core_interfaces"]) == 2
        assert len(doc["risk_warnings"]) == 1
        assert "generated_at" in doc

        for iface in doc["core_interfaces"]:
            assert "is_confirmed" in iface


class TestGenerateDocumentMissingProductDesign:
    """T13: BNDRY/edge — missing 产品设计 output."""

    def test_missing_product_design(self, handler, db_session, requirement_in_design):
        now = datetime.now(timezone.utc)
        outputs = [
            DesignResults(
                requirement_id="REQ-20260708-001",
                agent_role="技术选型",
                document_url="",
                skeleton_dirs=["src/a"],
                core_interfaces=[{"module": "a", "method": "fn"}],
                created_at=now,
                version=1,
            ),
        ]
        for o in outputs:
            db_session.add(o)
        db_session.commit()

        doc_str = handler._generate_document("REQ-20260708-001", 1, outputs)
        doc = json.loads(doc_str)

        assert doc["design_content"] == ""
        assert doc["skeleton_dirs"] == ["src/a"]


# ----- Edge Cases -----


class TestCompleteDesignWrongState:
    """T05: FUNC/error — requirement in REJECTED state cannot transition."""

    def test_wrong_state_raises(self, handler, requirement_rejected, db_session):
        from app.core.state_machine import InvalidTransitionError

        now = datetime.now(timezone.utc)
        outputs = [
            DesignResults(
                requirement_id="REQ-20260708-002",
                agent_role="产品设计",
                document_url="design doc",
                created_at=now,
                version=1,
            ),
        ]
        for o in outputs:
            db_session.add(o)
        db_session.commit()

        with pytest.raises(InvalidTransitionError):
            handler.complete_design("REQ-20260708-002")
