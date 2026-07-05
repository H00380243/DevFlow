"""Tests for app.models — SQLAlchemy 2.0 declarative models (Feature 2).

Covers Test Inventory rows A-X of F002 data-model design doc:
- A-I: FUNC/happy (model instantiation + persistence + relationship load + init_db idempotent)
- J-Q: FUNC/error (IntegrityError: NOT NULL / CHECK 1-5 / CHECK verdict / FK / CHECK id GLOB / CHECK timeout_count)
- R-X: BNDRY/edge (rating bounds 1/5, empty JSON, version=0, timeout_count=0, TTL boundary, 4-digit seq)

SEC: N/A — model layer has no user input surface; constraints enforced at DB
layer via CHECK/FK/NOT NULL. Inputs here are test fixtures, not request data.
"""

import datetime as dt

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# SEC: N/A — model layer has no user input surface (ORM column definitions only).


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _engine(tmp_path):
    """Isolated file-based SQLite engine with FK enforcement enabled (per test)."""
    db_path = tmp_path / "test_models.db"
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    # Enable FK enforcement on every connection (SQLite default is OFF).
    from sqlalchemy import event
    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    return eng


@pytest.fixture
def engine(tmp_path):
    eng = _engine(tmp_path)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    from app.models import Base, init_db
    init_db(engine)
    s = Session(bind=engine)
    yield s
    s.close()


def _make_requirement(session, rid="REQ-20260705-001"):
    """Insert a parent Requirements row and return it."""
    from app.models import Requirements
    req = Requirements(
        id=rid,
        original_text="原始需求文本",
        summary="核心诉求",
        submitter_id="u1",
        submitter_name="张三",
        tags=["bug", "ui"],
        estimated_scope="前端",
        current_stage="received",
        current_status="pending",
    )
    session.add(req)
    session.commit()
    return req


# ---------------------------------------------------------------------------
# A-I: FUNC/happy
# ---------------------------------------------------------------------------


class TestRequirementsHappy:
    """Row A — Requirements instantiation + persistence."""

    def test_requirements_persists_and_fields_roundtrip(self, session):
        """FUNC/happy A: Requirements row persists; fields map 1:1; id is PK."""
        req = _make_requirement(session, rid="REQ-20260705-001")
        from app.models import Requirements
        loaded = session.get(Requirements, "REQ-20260705-001")
        assert loaded is not None
        assert loaded.id == "REQ-20260705-001"
        assert loaded.original_text == "原始需求文本"
        assert loaded.summary == "核心诉求"
        assert loaded.submitter_id == "u1"
        assert loaded.submitter_name == "张三"
        assert loaded.tags == ["bug", "ui"]  # JSON round-trips as list
        assert loaded.estimated_scope == "前端"
        assert loaded.current_stage == "received"
        assert loaded.current_status == "pending"
        # PK constraint: duplicate id must be rejected
        dup = Requirements(id="REQ-20260705-001", original_text="x")
        session.add(dup)
        with pytest.raises(IntegrityError):
            session.commit()


class TestReviewResultsHappy:
    """Row B — ReviewResults + relationship to Requirements."""

    def test_review_results_persists_and_relationship_loads(self, session):
        """FUNC/happy B: ReviewResults persists; requirement.review_results list contains row."""
        req = _make_requirement(session)
        from app.models import ReviewResults
        review = ReviewResults(
            requirement_id=req.id,
            agent_role="business",
            business_value=3,
            technical_feasibility=4,
            roi=5,
            system_compatibility=2,
            verdict="通过",
            comments="通过评审",
        )
        session.add(review)
        session.commit()
        # Relationship: parent → child
        assert len(req.review_results) == 1
        assert req.review_results[0].business_value == 3
        assert req.review_results[0].verdict == "通过"
        # Relationship: child → parent (back_populates)
        assert review.requirement is req


class TestDesignResultsHappy:
    """Row C — DesignResults + relationship."""

    def test_design_results_persists_and_version_readable(self, session):
        """FUNC/happy C: DesignResults persists; requirement.design_results contains row; version readable."""
        req = _make_requirement(session)
        from app.models import DesignResults
        design = DesignResults(
            requirement_id=req.id,
            agent_role="tech",
            document_url="https://example.com/doc.md",
            skeleton_dirs=["src", "tests"],
            core_interfaces=["IF1", "IF2"],
            risk_warnings=["risk-a"],
            version=1,
        )
        session.add(design)
        session.commit()
        assert len(req.design_results) == 1
        assert req.design_results[0].version == 1
        assert req.design_results[0].skeleton_dirs == ["src", "tests"]
        assert req.design_results[0].core_interfaces == ["IF1", "IF2"]
        assert req.design_results[0].risk_warnings == ["risk-a"]


class TestImplementationResultsHappy:
    """Row D — ImplementationResults + relationship."""

    def test_implementation_results_persists_and_relationship(self, session):
        """FUNC/happy D: ImplementationResults persists; relationship loads."""
        req = _make_requirement(session)
        from app.models import ImplementationResults
        impl = ImplementationResults(
            requirement_id=req.id,
            code_files=["main.py", "utils.py"],
            verification_result={"passed": True, "errors": []},
            branch_name="feature-x",
            commit_id="abc123",
            commit_message="feat: add x",
        )
        session.add(impl)
        session.commit()
        assert len(req.implementation_results) == 1
        assert req.implementation_results[0].code_files == ["main.py", "utils.py"]
        assert req.implementation_results[0].verification_result == {"passed": True, "errors": []}
        assert req.implementation_results[0].branch_name == "feature-x"


class TestDeliveryArchivesHappy:
    """Row E — DeliveryArchives + relationship."""

    def test_delivery_archives_persists_and_relationship(self, session):
        """FUNC/happy E: DeliveryArchives persists; relationship loads."""
        req = _make_requirement(session)
        from app.models import DeliveryArchives
        archive = DeliveryArchives(
            requirement_id=req.id,
            review_ref="rev-1",
            design_ref="des-1",
            implementation_ref="impl-1",
            summary="交付完毕",
        )
        session.add(archive)
        session.commit()
        assert len(req.delivery_archives) == 1
        assert req.delivery_archives[0].summary == "交付完毕"
        assert req.delivery_archives[0].review_ref == "rev-1"


class TestStatusHistoryHappy:
    """Row F — StatusHistory + relationship."""

    def test_status_history_persists_and_relationship(self, session):
        """FUNC/happy F: StatusHistory persists; relationship loads."""
        req = _make_requirement(session)
        from app.models import StatusHistory
        hist = StatusHistory(
            requirement_id=req.id,
            from_status="pending",
            to_status="reviewing",
            trigger_event="submit",
            trigger_user="u1",
        )
        session.add(hist)
        session.commit()
        assert len(req.status_history) == 1
        assert req.status_history[0].from_status == "pending"
        assert req.status_history[0].to_status == "reviewing"
        assert req.status_history[0].trigger_event == "submit"


class TestArbitrationRequestsHappy:
    """Row G — ArbitrationRequests + relationship."""

    def test_arbitration_requests_persists_and_relationship(self, session):
        """FUNC/happy G: ArbitrationRequests persists; relationship loads."""
        req = _make_requirement(session)
        from app.models import ArbitrationRequests
        arb = ArbitrationRequests(
            requirement_id=req.id,
            admin_id="admin-1",
            review_summary="分歧",
            timeout_count=0,
        )
        session.add(arb)
        session.commit()
        assert len(req.arbitration_requests) == 1
        assert req.arbitration_requests[0].timeout_count == 0
        assert req.arbitration_requests[0].admin_id == "admin-1"


class TestIdempotencyStoreHappy:
    """Row H — IdempotencyStore + composite index."""

    def test_idempotency_store_persists_and_composite_index_exists(self, session):
        """FUNC/happy H: IdempotencyStore persists; composite index on (sender_hash, content_hash) exists."""
        from app.models import IdempotencyStore
        entry = IdempotencyStore(
            sender_hash=hash("u1"),
            content_hash="abc123hash",
            requirement_id="REQ-20260705-001",
        )
        session.add(entry)
        session.commit()
        # Query back by composite key
        loaded = session.query(IdempotencyStore).filter_by(
            sender_hash=hash("u1"), content_hash="abc123hash"
        ).first()
        assert loaded is not None
        assert loaded.requirement_id == "REQ-20260705-001"
        # Composite index exists in table metadata
        from app.models import Base
        tbl = Base.metadata.tables["idempotency_store"]
        ix_cols = [tuple(c.name for c in ix.columns) for ix in tbl.indexes]
        assert ("sender_hash", "content_hash") in ix_cols


class TestInitDb:
    """Row I — init_db creates all 8 tables and is idempotent."""

    def test_init_db_creates_all_tables_and_is_idempotent(self, engine):
        """FUNC/happy I: init_db creates 8 tables; second call does not raise."""
        from app.models import Base, init_db
        init_db(engine)
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        expected = {
            "requirements", "review_results", "design_results",
            "implementation_results", "delivery_archives", "status_history",
            "arbitration_requests", "idempotency_store",
        }
        assert expected.issubset(tables), f"missing: {expected - tables}"
        # Idempotent: second call is a no-op, must not raise
        init_db(engine)

    def test_init_db_none_engine_raises_argument_error(self):
        """FUNC/error (IC init_db Raises): engine=None raises ArgumentError."""
        from sqlalchemy.exc import ArgumentError
        from app.models import init_db
        with pytest.raises(ArgumentError):
            init_db(None)


# ---------------------------------------------------------------------------
# J-Q: FUNC/error
# ---------------------------------------------------------------------------


class TestRequirementsErrors:
    """Rows J, Q — Requirements NOT NULL + id CHECK GLOB."""

    def test_requirements_id_none_raises(self, session):
        """FUNC/error J: Requirements(id=None) raises IntegrityError (NOT NULL)."""
        from app.models import Requirements
        session.add(Requirements(original_text="x"))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_requirements_id_bad_format_raises(self, session):
        """FUNC/error Q: Requirements(id='INVALID-FORMAT') raises IntegrityError (CHECK GLOB)."""
        from app.models import Requirements
        session.add(Requirements(id="INVALID-FORMAT", original_text="x"))
        with pytest.raises(IntegrityError):
            session.commit()


class TestReviewResultsErrors:
    """Rows K, L, M, N, O — ReviewResults CHECK / FK / NOT NULL."""

    def test_review_business_value_above_5_raises(self, session):
        """FUNC/error K: business_value=6 raises (CHECK BETWEEN 1 AND 5)."""
        _make_requirement(session)
        from app.models import ReviewResults
        session.add(ReviewResults(
            requirement_id="REQ-20260705-001", business_value=6,
            technical_feasibility=3, roi=3, system_compatibility=3,
            verdict="通过",
        ))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_review_business_value_below_1_raises(self, session):
        """FUNC/error L: business_value=0 raises (CHECK lower bound)."""
        _make_requirement(session)
        from app.models import ReviewResults
        session.add(ReviewResults(
            requirement_id="REQ-20260705-001", business_value=0,
            technical_feasibility=3, roi=3, system_compatibility=3,
            verdict="通过",
        ))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_review_invalid_verdict_raises(self, session):
        """FUNC/error M: verdict='invalid' raises (CHECK IN 通过/反对/中立)."""
        _make_requirement(session)
        from app.models import ReviewResults
        session.add(ReviewResults(
            requirement_id="REQ-20260705-001", business_value=3,
            technical_feasibility=3, roi=3, system_compatibility=3,
            verdict="invalid",
        ))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_review_nonexistent_requirement_id_raises(self, session):
        """FUNC/error N: requirement_id pointing to non-existent parent raises (FK)."""
        from app.models import ReviewResults
        session.add(ReviewResults(
            requirement_id="REQ-DOES-NOT-EXIST", business_value=3,
            technical_feasibility=3, roi=3, system_compatibility=3,
            verdict="通过",
        ))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_review_requirement_id_none_raises(self, session):
        """FUNC/error O: requirement_id=None raises (NOT NULL)."""
        from app.models import ReviewResults
        session.add(ReviewResults(
            business_value=3, technical_feasibility=3, roi=3,
            system_compatibility=3, verdict="通过",
        ))
        with pytest.raises(IntegrityError):
            session.commit()


class TestArbitrationRequestsErrors:
    """Row P — timeout_count CHECK >= 0."""

    def test_arbitration_negative_timeout_count_raises(self, session):
        """FUNC/error P: timeout_count=-1 raises (CHECK >= 0)."""
        _make_requirement(session)
        from app.models import ArbitrationRequests
        session.add(ArbitrationRequests(
            requirement_id="REQ-20260705-001", admin_id="a1",
            timeout_count=-1,
        ))
        with pytest.raises(IntegrityError):
            session.commit()


# ---------------------------------------------------------------------------
# R-X: BNDRY/edge
# ---------------------------------------------------------------------------


class TestReviewResultsBoundaries:
    """Rows R, S — rating boundaries 1 and 5."""

    def test_review_all_ratings_at_lower_bound_1_persists(self, session):
        """BNDRY/edge R: all four ratings = 1 persists successfully."""
        req = _make_requirement(session)
        from app.models import ReviewResults
        review = ReviewResults(
            requirement_id=req.id, agent_role="business",
            business_value=1, technical_feasibility=1, roi=1,
            system_compatibility=1, verdict="中立",
        )
        session.add(review)
        session.commit()
        assert req.review_results[0].business_value == 1
        assert req.review_results[0].roi == 1

    def test_review_all_ratings_at_upper_bound_5_persists(self, session):
        """BNDRY/edge S: all four ratings = 5 persists successfully."""
        req = _make_requirement(session)
        from app.models import ReviewResults
        review = ReviewResults(
            requirement_id=req.id, agent_role="business",
            business_value=5, technical_feasibility=5, roi=5,
            system_compatibility=5, verdict="通过",
        )
        session.add(review)
        session.commit()
        assert req.review_results[0].business_value == 5
        assert req.review_results[0].system_compatibility == 5


class TestRequirementsJsonBoundary:
    """Row T — empty JSON array."""

    def test_requirements_empty_tags_json_persists(self, session):
        """BNDRY/edge T: tags=[] persists; query returns []."""
        from app.models import Requirements
        req = Requirements(
            id="REQ-20260705-002", original_text="x",
            submitter_id="u1", current_stage="received", current_status="pending",
            tags=[],
        )
        session.add(req)
        session.commit()
        loaded = session.get(Requirements, "REQ-20260705-002")
        assert loaded.tags == []


class TestDesignResultsVersionBoundary:
    """Row U — version=0 boundary."""

    def test_design_version_zero_persists(self, session):
        """BNDRY/edge U: version=0 persists (no CHECK lower bound; semantics owned by F012)."""
        req = _make_requirement(session)
        from app.models import DesignResults
        design = DesignResults(
            requirement_id=req.id, agent_role="tech",
            version=0,
        )
        session.add(design)
        session.commit()
        assert req.design_results[0].version == 0


class TestArbitrationTimeoutBoundary:
    """Row V — timeout_count=0 boundary."""

    def test_arbitration_timeout_zero_persists(self, session):
        """BNDRY/edge V: timeout_count=0 persists (CHECK >= 0 accepts 0)."""
        req = _make_requirement(session)
        from app.models import ArbitrationRequests
        arb = ArbitrationRequests(
            requirement_id=req.id, admin_id="a1", timeout_count=0,
        )
        session.add(arb)
        session.commit()
        assert req.arbitration_requests[0].timeout_count == 0


class TestIdempotencyTtlBoundary:
    """Row W — created_at TTL boundary."""

    def test_idempotency_created_at_old_timestamp_persists(self, session):
        """BNDRY/edge W: created_at = now-5min persists (TTL cleanup logic not F002's job)."""
        from app.models import IdempotencyStore
        old = dt.datetime.now() - dt.timedelta(minutes=5)
        entry = IdempotencyStore(
            sender_hash=1, content_hash="h", requirement_id="REQ-20260705-001",
            created_at=old,
        )
        session.add(entry)
        session.commit()
        loaded = session.query(IdempotencyStore).filter_by(content_hash="h").first()
        assert loaded is not None
        # Timestamp stored within 1-second tolerance (SQLite stores naive datetimes)
        assert loaded.created_at is not None
        assert abs((loaded.created_at - old).total_seconds()) < 1


class TestRequirementsIdFourDigitSeq:
    """Row X — 4-digit sequence (FR-002 expansion)."""

    def test_requirements_id_four_digit_sequence_persists(self, session):
        """BNDRY/edge X: id='REQ-20260705-9999' persists (CHECK GLOB accepts 4-digit)."""
        from app.models import Requirements
        req = Requirements(
            id="REQ-20260705-9999", original_text="x",
            submitter_id="u1", current_stage="received", current_status="pending",
        )
        session.add(req)
        session.commit()
        assert session.get(Requirements, "REQ-20260705-9999") is not None
