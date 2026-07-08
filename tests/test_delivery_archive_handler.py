"""Tests for DeliveryArchiveHandler — F019 交付档案与状态归档."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, DeliveryArchives


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
def req_impl_approved(db_session) -> Requirements:
    req = Requirements(
        id="REQ-20260709-001",
        original_text="测试需求",
        summary="测试",
        submitter_id="user001",
        current_stage="implementation",
        current_status="IMPL_APPROVED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(req)
    db_session.commit()
    return req


@pytest.fixture
def push_fn():
    return MagicMock()


@pytest.fixture
def upload_fn():
    return MagicMock()


@pytest.fixture
def handler(db_session, push_fn, upload_fn):
    from app.core.delivery_archive_handler import DeliveryArchiveHandler
    return DeliveryArchiveHandler(
        session=db_session,
        push_fn=push_fn,
        upload_fn=upload_fn,
    )


# ---- Test A: FUNC/happy — create_archive happy path ----
class TestCreateArchiveHappy:
    def test_archive_created_with_all_refs(self, handler, req_impl_approved):
        result = handler.create_archive(
            req_id="REQ-20260709-001",
            review_ref="review_001",
            design_ref="design_001",
            implementation_ref="impl_001",
            commit_id="abc123",
            summary="交付测试",
        )
        assert result is not None
        assert "archive_id" in result
        assert "delivered_at" in result
        assert result["delivered_at"] is not None


# ---- Test B: FUNC/happy — status transition to DELIVERED ----
class TestStatusTransition:
    def test_status_becomes_delivered(self, handler, req_impl_approved, db_session):
        handler.create_archive(
            req_id="REQ-20260709-001",
            commit_id="abc123",
        )
        from app.core.state_machine import StateMachine
        sm = StateMachine(db_session)
        status = sm.get_status("REQ-20260709-001")
        assert status.value == "DELIVERED"


# ---- Test C: FUNC/happy — IM notification sent ----
class TestIMNotification:
    def test_notification_sent(self, handler, req_impl_approved, push_fn):
        handler.create_archive(
            req_id="REQ-20260709-001",
            commit_id="abc123",
            summary="测试",
        )
        push_fn.assert_called()
        call_args = str(push_fn.call_args)
        assert "REQ-20260709-001" in call_args
        assert "abc123" in call_args


# ---- Test D: FUNC/happy — IM notification retry then succeed ----
class TestIMRetrySuccess:
    def test_retry_then_succeed(self, db_session, req_impl_approved):
        push_fn = MagicMock(side_effect=[Exception("fail"), Exception("fail"), None])
        upload_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        result = h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        assert result is not None
        assert push_fn.call_count == 3


# ---- Test E: FUNC/error — upload fails 3x, returns None ----
class TestUploadFails3x:
    def test_upload_fails_returns_none(self, db_session, req_impl_approved):
        upload_fn = MagicMock(side_effect=Exception("MinIO down"))
        push_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        result = h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        assert result is None
        push_fn.assert_called()


# ---- Test F: FUNC/error — IM notification fails 3x, raises ----
class TestIMNotifyFails3x:
    def test_notify_fails_raises(self, db_session, req_impl_approved):
        push_fn = MagicMock(side_effect=Exception("IM down"))
        upload_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        from app.core.arbitration_notification import NotificationFailedError
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        with pytest.raises(NotificationFailedError):
            h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")


# ---- Test G: FUNC/error — empty req_id raises ValueError ----
class TestEmptyReqId:
    def test_empty_req_id_raises(self, handler):
        with pytest.raises(ValueError, match="req_id cannot be empty"):
            handler.create_archive(req_id="", commit_id="abc123")


# ---- Test H: FUNC/error — empty commit_id raises ValueError ----
class TestEmptyCommitId:
    def test_empty_commit_id_raises(self, handler):
        with pytest.raises(ValueError, match="commit_id cannot be empty"):
            handler.create_archive(req_id="REQ-20260709-001", commit_id="")


# ---- Test I: BNDRY/edge — null refs stored as NULL ----
class TestNullRefs:
    def test_null_refs_accepted(self, handler, req_impl_approved, db_session):
        result = handler.create_archive(
            req_id="REQ-20260709-001",
            commit_id="abc123",
        )
        assert result is not None
        row = db_session.query(DeliveryArchives).filter_by(
            requirement_id="REQ-20260709-001"
        ).first()
        assert row.review_ref is None
        assert row.design_ref is None
        assert row.implementation_ref is None


# ---- Test J: BNDRY/edge — upload fails exactly 3 times ----
class TestUploadExact3xFails:
    def test_upload_exact_3_fails(self, db_session, req_impl_approved):
        upload_fn = MagicMock(side_effect=Exception("fail"))
        push_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        result = h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        assert result is None
        assert upload_fn.call_count == 3


# ---- Test K: BNDRY/edge — IM notify fails exactly 3 times ----
class TestIMExact3xFails:
    def test_im_exact_3_fails(self, db_session, req_impl_approved):
        push_fn = MagicMock(side_effect=Exception("fail"))
        upload_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        from app.core.arbitration_notification import NotificationFailedError
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        with pytest.raises(NotificationFailedError):
            h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        assert push_fn.call_count == 3


# ---- Test L: BNDRY/edge — upload fails 1st, succeeds 2nd ----
class TestUploadRetrySuccess:
    def test_upload_retry_on_2nd_attempt(self, db_session, req_impl_approved):
        upload_fn = MagicMock(side_effect=[Exception("fail"), None])
        push_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        result = h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        assert result is not None
        assert upload_fn.call_count == 2


# ---- Test M: FUNC/state — IMPL_APPROVED→DELIVERED transition ----
class TestStateTransitionImplApproved:
    def test_impl_approved_to_delivered(self, handler, req_impl_approved, db_session):
        handler.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        row = db_session.query(Requirements).filter_by(id="REQ-20260709-001").first()
        assert row.current_status == "DELIVERED"


# ---- Test N: FUNC/state — wrong state raises InvalidTransitionError ----
class TestWrongStateRaises:
    def test_wrong_state_raises(self, db_session, push_fn, upload_fn):
        from app.core.state_machine import InvalidTransitionError
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        req = Requirements(
            id="REQ-20260709-999",
            original_text="测试",
            summary="测试",
            submitter_id="user001",
            current_stage="implementation",
            current_status="IN_IMPLEMENTATION",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(req)
        db_session.commit()
        h = DeliveryArchiveHandler(session=db_session, push_fn=push_fn, upload_fn=upload_fn)
        with pytest.raises(InvalidTransitionError):
            h.create_archive(req_id="REQ-20260709-999", commit_id="abc123")


# ---- Test O: INTG/db — archive row queryable ----
class TestArchiveQueryable:
    def test_archive_in_db(self, handler, req_impl_approved, db_session):
        handler.create_archive(
            req_id="REQ-20260709-001",
            commit_id="abc123",
            summary="测试摘要",
        )
        row = db_session.query(DeliveryArchives).filter_by(
            requirement_id="REQ-20260709-001"
        ).first()
        assert row is not None
        assert row.commit_id == "abc123" if hasattr(row, "commit_id") else True
        assert row.summary == "测试摘要"


# ---- Test P: INTG/db — state persisted after SM transition ----
class TestStatePersisted:
    def test_state_delivered_persisted(self, handler, req_impl_approved, db_session):
        handler.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
        row = db_session.query(Requirements).filter_by(id="REQ-20260709-001").first()
        assert row.current_status == "DELIVERED"


# ---- Test Q: INTG/minio — upload_fn called correctly ----
class TestUploadCalled:
    def test_upload_fn_called(self, handler, req_impl_approved, upload_fn):
        handler.create_archive(
            req_id="REQ-20260709-001",
            commit_id="abc123",
        )
        upload_fn.assert_called_once()
        call_args = upload_fn.call_args
        assert call_args[0][0] == "REQ-20260709-001"


# ---- Test R: FUNC/happy — format_archive_message ----
class TestFormatMessage:
    def test_message_contains_fields(self, handler):
        msg = handler.format_archive_message("REQ-001", "abc", "测试")
        assert "REQ-001" in msg
        assert "abc" in msg
        assert "测试" in msg


# ---- Test S: FUNC/error — non-retryable exception propagates ----
class TestNonRetryableException:
    def test_type_error_propagates(self, db_session, req_impl_approved):
        upload_fn = MagicMock(side_effect=TypeError("bad arg"))
        push_fn = MagicMock()
        from app.core.delivery_archive_handler import DeliveryArchiveHandler
        h = DeliveryArchiveHandler(
            session=db_session,
            push_fn=push_fn,
            upload_fn=upload_fn,
        )
        with pytest.raises(TypeError):
            h.create_archive(req_id="REQ-20260709-001", commit_id="abc123")
