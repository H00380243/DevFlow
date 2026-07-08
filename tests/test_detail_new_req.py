"""Test detail page for manually created requirements."""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Requirements, DesignResults


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


def test_manually_created_requirement_detail(db_session):
    from app.core.requirements_service import RequirementsService
    from app.core.requirement_detail_service import RequirementDetailService

    created = RequirementsService.create_requirement(
        db_session,
        original_text="手动添加的测试需求",
        summary="测试摘要",
        submitter_id="user001",
        submitter_name="张三",
        tags=["紧急"],
    )

    detail = RequirementDetailService.get_detail(db_session, created["id"])
    assert detail["id"] == created["id"]
    assert detail["summary"] == "测试摘要"
    assert detail["original_text"] == "手动添加的测试需求"
    assert detail["submitter_id"] == "user001"
    assert detail["submitter_name"] == "张三"
    assert detail["tags"] == ["紧急"]
    assert detail["current_stage"] == "review"
    assert detail["current_status"] == "PENDING_REVIEW"
    assert detail["timeline"] == []
    assert detail["review_details"] == []
    assert detail["design_details"] == []
    assert detail["implementation_details"] == []
