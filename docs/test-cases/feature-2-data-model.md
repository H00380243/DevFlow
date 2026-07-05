# Feature-Level ST Test Case Document: 数据模型与迁移 (F002)

**Feature ID**: 2
**Feature Title**: 数据模型与迁移
**Related Requirements**: N/A (srs_trace is empty — infrastructure feature per design)
**Date**: 2026-07-05
**Standard**: ISO/IEC/IEEE 29119-3
**Design Reference**: docs/features/2026-07-05-F002-data-model.md

**Specification resolutions applied from Feature Design Clarification Addendum.**
- #1: IdempotencyStore.requirement_id is a soft reference (no FK constraint)
- #2: JSON fields use SQLAlchemy JSON type (SQLite TEXT storage)
- #3: Requirements.id CHECK GLOB uses canonical REQ-YYYYMMDD-NNN format
- #4: TTL cleanup logic not implemented in F002 (only created_at column provided)
- #5: verdict CHECK IN ('通过','反对','中立')
- #6: timeout_count CHECK >= 0

---

## 1. Summary Table

| Category | Abbreviation | Count |
|----------|-------------|-------|
| Functional | FUNC | 21 |
| Boundary | BNDRY | 7 |
| UI | UI | 0 |
| Security | SEC | 0 |
| Performance | PERF | 0 |
| **Total** | | **28** |

---

## 2. Test Cases

---

### ST-FUNC-002-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-001 |
| **Test Objective** | Requirements model instantiation, persistence, and field roundtrip |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `Requirements`, Test Inventory Row A |
| **Preconditions** | SQLite engine created with FK enforcement enabled; `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `Requirements(id="REQ-20260705-001", original_text="原始需求文本", summary="核心诉求", submitter_id="u1", submitter_name="张三", tags=["bug","ui"], estimated_scope="前端", current_stage="received", current_status="pending")` | Object created without error |
| 2 | `session.add(req); session.commit()` | Commit succeeds |
| 3 | `session.get(Requirements, "REQ-20260705-001")` | Returns row with all fields matching input; `tags` deserialized as `["bug","ui"]` |
| 4 | Insert duplicate `Requirements(id="REQ-20260705-001", original_text="x")` and commit | `IntegrityError` raised (PK violation) |

---

### ST-FUNC-002-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-002 |
| **Test Objective** | ReviewResults persistence and bidirectional relationship load |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ReviewResults`, Test Inventory Row B |
| **Preconditions** | Parent Requirements row exists; `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(requirement_id="REQ-20260705-001", agent_role="business", business_value=3, technical_feasibility=4, roi=5, system_compatibility=2, verdict="通过", comments="通过评审")` | Object created |
| 2 | `session.add(review); session.commit()` | Commit succeeds |
| 3 | Check `req.review_results` list | Contains exactly 1 row; `business_value == 3`, `verdict == "通过"` |
| 4 | Check `review.requirement` | Returns the parent Requirements object (back_populates) |

---

### ST-FUNC-002-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-003 |
| **Test Objective** | DesignResults persistence, version read, and relationship load |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `DesignResults`, Test Inventory Row C |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `DesignResults(requirement_id=parent_id, agent_role="tech", document_url="https://example.com/doc.md", skeleton_dirs=["src","tests"], core_interfaces=["IF1","IF2"], risk_warnings=["risk-a"], version=1)` | Object created |
| 2 | `session.add(design); session.commit()` | Commit succeeds |
| 3 | Check `req.design_results` | Contains 1 row; `version == 1`; JSON fields deserialize correctly |
| 4 | Check `design.requirement` | Returns parent Requirements |

---

### ST-FUNC-002-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-004 |
| **Test Objective** | ImplementationResults persistence and relationship load |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ImplementationResults`, Test Inventory Row D |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ImplementationResults(requirement_id=parent_id, code_files=["main.py","utils.py"], verification_result={"passed":True,"errors":[]}, branch_name="feature-x", commit_id="abc123", commit_message="feat: add x")` | Object created |
| 2 | `session.add(impl); session.commit()` | Commit succeeds |
| 3 | Check `req.implementation_results` | Contains 1 row; JSON fields roundtrip correctly |

---

### ST-FUNC-002-005

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-005 |
| **Test Objective** | DeliveryArchives persistence and relationship load |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `DeliveryArchives`, Test Inventory Row E |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `DeliveryArchives(requirement_id=parent_id, review_ref="rev-1", design_ref="des-1", implementation_ref="impl-1", summary="交付完毕")` | Object created |
| 2 | `session.add(archive); session.commit()` | Commit succeeds |
| 3 | Check `req.delivery_archives` | Contains 1 row; `summary == "交付完毕"` |

---

### ST-FUNC-002-006

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-006 |
| **Test Objective** | StatusHistory persistence and relationship load |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `StatusHistory`, Test Inventory Row F |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `StatusHistory(requirement_id=parent_id, from_status="pending", to_status="reviewing", trigger_event="submit", trigger_user="u1")` | Object created |
| 2 | `session.add(hist); session.commit()` | Commit succeeds |
| 3 | Check `req.status_history` | Contains 1 row; all fields match |

---

### ST-FUNC-002-007

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-007 |
| **Test Objective** | ArbitrationRequests persistence and relationship load |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ArbitrationRequests`, Test Inventory Row G |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ArbitrationRequests(requirement_id=parent_id, admin_id="admin-1", review_summary="分歧", timeout_count=0)` | Object created |
| 2 | `session.add(arb); session.commit()` | Commit succeeds |
| 3 | Check `req.arbitration_requests` | Contains 1 row; `timeout_count == 0` |

---

### ST-FUNC-002-008

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-008 |
| **Test Objective** | IdempotencyStore persistence and composite index availability |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `IdempotencyStore`, Test Inventory Row H |
| **Preconditions** | `init_db(engine)` called; IdempotencyStore has composite index on (sender_hash, content_hash) |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `IdempotencyStore(sender_hash=hash("u1"), content_hash="abc123hash", requirement_id="REQ-20260705-001")` | Object created |
| 2 | `session.add(entry); session.commit()` | Commit succeeds |
| 3 | Query by `sender_hash=hash("u1"), content_hash="abc123hash"` | Returns the entry; `requirement_id` matches |
| 4 | Inspect table metadata for composite index on `(sender_hash, content_hash)` | Index exists |

---

### ST-FUNC-002-009

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-009 |
| **Test Objective** | init_db creates all 8 tables and is idempotent |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `init_db`, Test Inventory Row I |
| **Preconditions** | Fresh SQLite engine |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | `init_db(engine)` | Returns without error |
| 2 | Inspect `sqlite_master` for table names | Contains all 8 tables: requirements, review_results, design_results, implementation_results, delivery_archives, status_history, arbitration_requests, idempotency_store |
| 3 | `init_db(engine)` again (second call) | No error raised (idempotent) |

---

### ST-FUNC-002-010

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-010 |
| **Test Objective** | init_db with None engine raises ArgumentError |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `init_db` Raises |
| **Preconditions** | None |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `init_db(None)` | `ArgumentError` raised |

---

### ST-FUNC-002-011

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-011 |
| **Test Objective** | Requirements(id=None) raises IntegrityError (NOT NULL) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `Requirements` Raises, Test Inventory Row J |
| **Preconditions** | `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `Requirements(original_text="x")` (no id) and commit | `IntegrityError` raised (NOT NULL constraint on id) |

---

### ST-FUNC-002-012

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-012 |
| **Test Objective** | ReviewResults(business_value=6) raises IntegrityError (CHECK BETWEEN 1 AND 5) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ReviewResults` Raises, Test Inventory Row K |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(business_value=6, technical_feasibility=3, roi=3, system_compatibility=3, verdict="通过")` and commit | `IntegrityError` raised (CHECK constraint) |

---

### ST-FUNC-002-013

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-013 |
| **Test Objective** | ReviewResults(business_value=0) raises IntegrityError (CHECK lower bound) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ReviewResults` Raises, Test Inventory Row L |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(business_value=0, technical_feasibility=3, roi=3, system_compatibility=3, verdict="通过")` and commit | `IntegrityError` raised (CHECK constraint) |

---

### ST-FUNC-002-014

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-014 |
| **Test Objective** | ReviewResults(verdict="invalid") raises IntegrityError (CHECK IN) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ReviewResults` Raises, Test Inventory Row M |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(verdict="invalid", business_value=3, technical_feasibility=3, roi=3, system_compatibility=3)` and commit | `IntegrityError` raised (verdict CHECK) |

---

### ST-FUNC-002-015

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-015 |
| **Test Objective** | ReviewResults(requirement_id="REQ-NONEXIST") raises IntegrityError (FK) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ReviewResults` Raises, Test Inventory Row N |
| **Preconditions** | `init_db(engine)` called; FK enforcement enabled |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(requirement_id="REQ-DOES-NOT-EXIST", business_value=3, technical_feasibility=3, roi=3, system_compatibility=3, verdict="通过")` and commit | `IntegrityError` raised (FK violation) |

---

### ST-FUNC-002-016

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-016 |
| **Test Objective** | ReviewResults(requirement_id=None) raises IntegrityError (NOT NULL) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ReviewResults` Raises, Test Inventory Row O |
| **Preconditions** | `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(business_value=3, technical_feasibility=3, roi=3, system_compatibility=3, verdict="通过")` (no requirement_id) and commit | `IntegrityError` raised (NOT NULL) |

---

### ST-FUNC-002-017

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-017 |
| **Test Objective** | ArbitrationRequests(timeout_count=-1) raises IntegrityError (CHECK >= 0) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ArbitrationRequests` Raises, Test Inventory Row P |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ArbitrationRequests(requirement_id=parent_id, admin_id="a1", timeout_count=-1)` and commit | `IntegrityError` raised (CHECK >= 0) |

---

### ST-FUNC-002-018

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-018 |
| **Test Objective** | Requirements(id="INVALID-FORMAT") raises IntegrityError (CHECK GLOB) |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `Requirements` Raises, Test Inventory Row Q |
| **Preconditions** | `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `Requirements(id="INVALID-FORMAT", original_text="x", submitter_id="u1", current_stage="received", current_status="pending")` and commit | `IntegrityError` raised (CHECK GLOB format) |

---

### ST-FUNC-002-019

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-019 |
| **Test Objective** | Real SQLite: init_db + insert + commit + relationship load + data persists on disk |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC + Real SQLite, Test Inventory Row Y |
| **Preconditions** | Real SQLite file on disk; `@pytest.mark.real` |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create real file-based SQLite engine; `init_db(engine)` | Tables created |
| 2 | Insert `Requirements` + `ReviewResults` via Session; commit | Rows persisted |
| 3 | Open fresh Session; `session.get(Requirements, "REQ-20260705-001")` | Returns row with `review_results` relationship loaded (1 child) |
| 4 | Verify DB file exists and `st_size > 0` | True — data physically on disk |

---

### ST-FUNC-002-020

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-020 |
| **Test Objective** | Alembic upgrade head creates all 8 tables + indexes on real SQLite |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `upgrade`, Test Inventory Row Z |
| **Preconditions** | Real SQLite file; `alembic.ini` + `alembic/` configured; `@pytest.mark.real` |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Run `alembic upgrade head` via subprocess with `DATABASE_URL` pointing to real SQLite file | Return code 0 |
| 2 | Inspect table names via `inspect(engine)` | Contains all 8 business tables + `alembic_version` |
| 3 | Check requirements indexes | `submitter_id` index exists; `(current_stage, current_status)` composite index exists |
| 4 | Check idempotency_store indexes | `(sender_hash, content_hash)` composite index exists |

---

### ST-FUNC-002-021

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-021 |
| **Test Objective** | Alembic upgrade→downgrade→upgrade round-trip is idempotent |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `downgrade` + idempotency, Test Inventory Row AA |
| **Preconditions** | Real SQLite file; `@pytest.mark.real` |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | `alembic upgrade head` | Return code 0; 8 tables created |
| 2 | `alembic downgrade base` | Return code 0; all business tables dropped |
| 3 | Inspect table names | No business tables remain |
| 4 | `alembic upgrade head` (second time) | Return code 0; tables recreated |
| 5 | Inspect table names | 8 tables present again (idempotent) |

---

### ST-FUNC-002-022

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-002-022 |
| **Test Objective** | Real SQLite FK enforcement on non-existent requirement_id |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC Real SQLite FK, Test Inventory Row AB |
| **Preconditions** | Real SQLite file; FK enforcement via PRAGMA; `@pytest.mark.real` |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create real SQLite engine with `PRAGMA foreign_keys=ON`; `init_db(engine)` | Tables created |
| 2 | `ReviewResults(requirement_id="REQ-NONEXISTENT", business_value=3, technical_feasibility=3, roi=3, system_compatibility=3, verdict="通过")` | Object created |
| 3 | `session.commit()` | `IntegrityError` raised (FK enforced by real SQLite) |

---

### ST-BNDRY-002-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-001 |
| **Test Objective** | ReviewResults all four ratings at lower bound (1) persists |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Algorithm Boundary, Test Inventory Row R |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(business_value=1, technical_feasibility=1, roi=1, system_compatibility=1, verdict="中立")` and commit | Commit succeeds |
| 2 | Query back | All four rating fields == 1 |

---

### ST-BNDRY-002-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-002 |
| **Test Objective** | ReviewResults all four ratings at upper bound (5) persists |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Algorithm Boundary, Test Inventory Row S |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewResults(business_value=5, technical_feasibility=5, roi=5, system_compatibility=5, verdict="通过")` and commit | Commit succeeds |
| 2 | Query back | All four rating fields == 5 |

---

### ST-BNDRY-002-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-003 |
| **Test Objective** | Requirements tags=[] (empty JSON array) persists |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `Requirements`, Test Inventory Row T |
| **Preconditions** | `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `Requirements(id="REQ-20260705-002", tags=[], submitter_id="u1", current_stage="received", current_status="pending")` and commit | Commit succeeds |
| 2 | Query back `tags` field | Returns `[]` (empty list) |

---

### ST-BNDRY-002-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-004 |
| **Test Objective** | DesignResults version=0 persists (no CHECK lower bound) |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `DesignResults`, Test Inventory Row U |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `DesignResults(requirement_id=parent_id, agent_role="tech", version=0)` and commit | Commit succeeds |
| 2 | Query back | `version == 0` |

---

### ST-BNDRY-002-005

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-005 |
| **Test Objective** | ArbitrationRequests timeout_count=0 persists (boundary of CHECK >= 0) |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `ArbitrationRequests`, Test Inventory Row V |
| **Preconditions** | Parent Requirements row exists |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ArbitrationRequests(requirement_id=parent_id, admin_id="a1", timeout_count=0)` and commit | Commit succeeds |
| 2 | Query back | `timeout_count == 0` |

---

### ST-BNDRY-002-006

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-006 |
| **Test Objective** | IdempotencyStore created_at = now-5min persists (TTL boundary) |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `IdempotencyStore`, Test Inventory Row W |
| **Preconditions** | `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `IdempotencyStore(sender_hash=1, content_hash="h", requirement_id="REQ-20260705-001", created_at=now-5min)` and commit | Commit succeeds |
| 2 | Query back `created_at` | Timestamp within 1-second tolerance of now-5min |

---

### ST-BNDRY-002-007

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-002-007 |
| **Test Objective** | Requirements id="REQ-20260705-9999" (4-digit sequence) persists |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §IC `Requirements`, Test Inventory Row X |
| **Preconditions** | `init_db(engine)` called |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `Requirements(id="REQ-20260705-9999", original_text="x", submitter_id="u1", current_stage="received", current_status="pending")` and commit | Commit succeeds (CHECK GLOB accepts 4-digit) |
| 2 | Query back | Row returned with `id == "REQ-20260705-9999"` |

---

## 3. Traceability Matrix

| Case ID | Requirement | Design Row | Automated Test | Result |
|---------|-------------|------------|----------------|--------|
| ST-FUNC-002-001 | N/A (srs_trace empty) | Row A | `tests/test_models.py::TestRequirementsHappy::test_requirements_persists_and_fields_roundtrip` | PASS |
| ST-FUNC-002-002 | N/A | Row B | `tests/test_models.py::TestReviewResultsHappy::test_review_results_persists_and_relationship_loads` | PASS |
| ST-FUNC-002-003 | N/A | Row C | `tests/test_models.py::TestDesignResultsHappy::test_design_results_persists_and_version_readable` | PASS |
| ST-FUNC-002-004 | N/A | Row D | `tests/test_models.py::TestImplementationResultsHappy::test_implementation_results_persists_and_relationship` | PASS |
| ST-FUNC-002-005 | N/A | Row E | `tests/test_models.py::TestDeliveryArchivesHappy::test_delivery_archives_persists_and_relationship` | PASS |
| ST-FUNC-002-006 | N/A | Row F | `tests/test_models.py::TestStatusHistoryHappy::test_status_history_persists_and_relationship` | PASS |
| ST-FUNC-002-007 | N/A | Row G | `tests/test_models.py::TestArbitrationRequestsHappy::test_arbitration_requests_persists_and_relationship` | PASS |
| ST-FUNC-002-008 | N/A | Row H | `tests/test_models.py::TestIdempotencyStoreHappy::test_idempotency_store_persists_and_composite_index_exists` | PASS |
| ST-FUNC-002-009 | N/A | Row I | `tests/test_models.py::TestInitDb::test_init_db_creates_all_tables_and_is_idempotent` | PASS |
| ST-FUNC-002-010 | N/A | (IC init_db) | `tests/test_models.py::TestInitDb::test_init_db_none_engine_raises_argument_error` | PASS |
| ST-FUNC-002-011 | N/A | Row J | `tests/test_models.py::TestRequirementsErrors::test_requirements_id_none_raises` | PASS |
| ST-FUNC-002-012 | N/A | Row K | `tests/test_models.py::TestReviewResultsErrors::test_review_business_value_above_5_raises` | PASS |
| ST-FUNC-002-013 | N/A | Row L | `tests/test_models.py::TestReviewResultsErrors::test_review_business_value_below_1_raises` | PASS |
| ST-FUNC-002-014 | N/A | Row M | `tests/test_models.py::TestReviewResultsErrors::test_review_invalid_verdict_raises` | PASS |
| ST-FUNC-002-015 | N/A | Row N | `tests/test_models.py::TestReviewResultsErrors::test_review_nonexistent_requirement_id_raises` | PASS |
| ST-FUNC-002-016 | N/A | Row O | `tests/test_models.py::TestReviewResultsErrors::test_review_requirement_id_none_raises` | PASS |
| ST-FUNC-002-017 | N/A | Row P | `tests/test_models.py::TestArbitrationRequestsErrors::test_arbitration_negative_timeout_count_raises` | PASS |
| ST-FUNC-002-018 | N/A | Row Q | `tests/test_models.py::TestRequirementsErrors::test_requirements_id_bad_format_raises` | PASS |
| ST-FUNC-002-019 | N/A | Row Y | `tests/test_migration.py::test_real_sqlite_create_all_and_relationship_load` | PASS |
| ST-FUNC-002-020 | N/A | Row Z | `tests/test_migration.py::test_real_alembic_upgrade_creates_all_tables_and_indexes` | PASS |
| ST-FUNC-002-021 | N/A | Row AA | `tests/test_migration.py::test_real_alembic_downgrade_then_upgrade_is_idempotent` | PASS |
| ST-FUNC-002-022 | N/A | Row AB | `tests/test_migration.py::test_real_sqlite_fk_enforced_on_nonexistent_requirement` | PASS |
| ST-BNDRY-002-001 | N/A | Row R | `tests/test_models.py::TestReviewResultsBoundaries::test_review_all_ratings_at_lower_bound_1_persists` | PASS |
| ST-BNDRY-002-002 | N/A | Row S | `tests/test_models.py::TestReviewResultsBoundaries::test_review_all_ratings_at_upper_bound_5_persists` | PASS |
| ST-BNDRY-002-003 | N/A | Row T | `tests/test_models.py::TestRequirementsJsonBoundary::test_requirements_empty_tags_json_persists` | PASS |
| ST-BNDRY-002-004 | N/A | Row U | `tests/test_models.py::TestDesignResultsVersionBoundary::test_design_version_zero_persists` | PASS |
| ST-BNDRY-002-005 | N/A | Row V | `tests/test_models.py::TestArbitrationTimeoutBoundary::test_arbitration_timeout_zero_persists` | PASS |
| ST-BNDRY-002-006 | N/A | Row W | `tests/test_models.py::TestIdempotencyTtlBoundary::test_idempotency_created_at_old_timestamp_persists` | PASS |
| ST-BNDRY-002-007 | N/A | Row X | `tests/test_models.py::TestRequirementsIdFourDigitSeq::test_requirements_id_four_digit_sequence_persists` | PASS |

---

## 4. Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 28 |
| Passed | 28 |
| Failed | 0 |
| Pending | 0 |

## 5. Manual Test Case Summary

| Metric | Value |
|--------|-------|
| Total Manual Cases | 0 |
| Pending-Manual | 0 |
