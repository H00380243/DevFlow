"""Tests for RequirementsService.create_requirement."""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements


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


class TestCreateRequirement:
    def test_create_simple(self, db_session):
        from app.core.requirements_service import RequirementsService
        result = RequirementsService.create_requirement(
            db_session,
            original_text="测试需求描述",
            summary="测试摘要",
            submitter_id="user001",
        )
        assert result["id"].startswith("REQ-")
        assert result["summary"] == "测试摘要"
        assert result["current_stage"] == "review"
        assert result["current_status"] == "PENDING_REVIEW"

        row = db_session.query(Requirements).filter(Requirements.id == result["id"]).first()
        assert row is not None
        assert row.original_text == "测试需求描述"

    def test_sequential_id(self, db_session):
        from app.core.requirements_service import RequirementsService
        r1 = RequirementsService.create_requirement(db_session, "a", "s1", "user001")
        r2 = RequirementsService.create_requirement(db_session, "b", "s2", "user001")
        seq1 = int(r1["id"].split("-")[-1])
        seq2 = int(r2["id"].split("-")[-1])
        assert seq2 == seq1 + 1

    def test_with_tags(self, db_session):
        from app.core.requirements_service import RequirementsService
        result = RequirementsService.create_requirement(
            db_session,
            original_text="带标签需求",
            summary="标签测试",
            submitter_id="user001",
            tags=["紧急", "前端"],
        )
        row = db_session.query(Requirements).filter(Requirements.id == result["id"]).first()
        assert row.tags == ["紧急", "前端"]

    def test_with_submitter_name(self, db_session):
        from app.core.requirements_service import RequirementsService
        result = RequirementsService.create_requirement(
            db_session,
            original_text="带名称",
            summary="名称测试",
            submitter_id="user001",
            submitter_name="张三",
        )
        row = db_session.query(Requirements).filter(Requirements.id == result["id"]).first()
        assert row.submitter_name == "张三"
