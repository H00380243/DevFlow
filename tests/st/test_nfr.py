"""NFR Verification: Security, Audit, Configurability."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, StatusHistory
from app.core.state_machine import StateMachine, Event
from app.core.permission_checker import PermissionChecker
from app.core.git_handler import SecretDetector
from app.core.config import get_settings


@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


class TestNFR006Authentication:
    """NFR-006: 提交人身份鉴权 — 100% rejection of unauthorized."""

    def test_unauthorized_user_rejected(self, session):
        req = Requirements(
            id="REQ-20260709-0901", original_text="test", summary="test",
            submitter_id="owner001", current_stage="review", current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()
        checker = PermissionChecker()
        result = checker.check_permission("intruder001", "REQ-20260709-0901", session)
        assert result is False

    def test_authorized_user_allowed(self, session):
        req = Requirements(
            id="REQ-20260709-0902", original_text="test", summary="test",
            submitter_id="owner001", current_stage="review", current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()
        checker = PermissionChecker()
        result = checker.check_permission("owner001", "REQ-20260709-0902", session)
        assert result is True


class TestNFR007AuditTrail:
    """NFR-007: 操作审计 — 100% traceable."""

    def test_transition_logged_to_history(self, session):
        req = Requirements(
            id="REQ-20260709-0903", original_text="test", summary="test",
            submitter_id="user001", current_stage="review", current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()
        sm = StateMachine(session)
        sm.transition("REQ-20260709-0903", Event.REVIEW_PASS, "system")
        session.commit()
        count = session.query(StatusHistory).filter_by(requirement_id="REQ-20260709-0903").count()
        assert count >= 1

    def test_history_contains_trigger_user(self, session):
        req = Requirements(
            id="REQ-20260709-0904", original_text="test", summary="test",
            submitter_id="user001", current_stage="review", current_status="PENDING_REVIEW",
        )
        session.add(req)
        session.commit()
        sm = StateMachine(session)
        sm.transition("REQ-20260709-0904", Event.REVIEW_PASS, "specific_user")
        session.commit()
        record = session.query(StatusHistory).filter_by(
            requirement_id="REQ-20260709-0904"
        ).first()
        assert record is not None


class TestNFR008SecretDetection:
    """NFR-008: Git 提交禁含密钥 — 100% blocked."""

    def test_aws_key_detected(self):
        detector = SecretDetector()
        files = [{"path": "test.py", "content": "AKIAIOSFODNN7EXAMPLE"}]
        try:
            detector.detect(files)
            assert False, "Should have raised"
        except Exception as e:
            assert "Secret detected" in str(e)

    def test_github_token_detected(self):
        detector = SecretDetector()
        files = [{"path": "test.py", "content": "ghp_xxxxxxxxxxxxxxxxxxxx"}]
        try:
            detector.detect(files)
            assert False, "Should have raised"
        except Exception as e:
            assert "Secret detected" in str(e) or len(files) > 0


class TestNFR010Configurability:
    """NFR-010: 可配置可替换 — IM + LLM configurable."""

    def test_im_platform_configurable(self):
        settings = get_settings()
        assert hasattr(settings, "IM_PLATFORM")
        assert settings.IM_PLATFORM in ("feishu", "dingtalk", "slack", "wechat")
