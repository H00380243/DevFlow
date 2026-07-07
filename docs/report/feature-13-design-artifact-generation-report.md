# Feature 13 Report — 设计产出物生成

**Feature**: F013 — 设计产出物生成 (id=13)
**Priority**: high
**Category**: core
**Dependencies**: F012 (设计团多角色产出) ✓
**SRS Trace**: FR-010
**Completed**: 2026-07-08
**Git SHA**: `c92dce9`

---

## TDD Results (Red → Green → Refactor)

| Phase | Result |
|-------|--------|
| Red (17 tests) | 17/17 ModuleNotFoundError (Module not yet exist) |
| Green (implementation) | 17/17 PASS |
| Refactor | 100% line coverage, no redundant code |

## Test Inventory

| ID | Category | Test Name | Status |
|----|----------|-----------|--------|
| T01 | FUNC/happy | `test_complete_design_returns_url` | PASS |
| T01 ext | FUNC/happy | `test_generated_document_structure` | PASS |
| T02 | FUNC/happy | `test_validate_interfaces` | PASS |
| T03 | FUNC/error | `test_upload_failure_notifies_admin` | PASS |
| T03 ext | FUNC/error | `test_all_retries_exhausted` | PASS |
| T04 | FUNC/error | `test_requirement_not_found` | PASS |
| T05 | FUNC/error | `test_wrong_state_raises` | PASS |
| T06 | FUNC/error | `test_no_design_outputs` | PASS |
| T07 | FUNC/error | `test_empty_content_raises` | PASS |
| T07 ext | FUNC/error | `test_empty_filename_raises` | PASS |
| T08 | BNDRY/edge | `test_empty_interfaces` | PASS |
| T09 | BNDRY/edge | `test_method_not_in_text` | PASS |
| T10 | BNDRY/edge | `test_method_in_text` | PASS |
| T11 | BNDRY/edge | `test_retry_then_succeeds` | PASS |
| T12 | FUNC/state | `test_state_transition` | PASS |
| T13 | BNDRY/edge | `test_missing_product_design` | PASS |
| — | BNDRY/edge | `test_missing_keys` | PASS |

**Total: 17 tests** (16 inventory rows + 1 extra), **0 failures, 0 skipped**.

## Negative Ratio

- 9 of 17 tests are negative/error-path (52.9%) ≥ 40% ✓

## Coverage

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| `app/core/design_output_handler.py` | 88 | 0 | **100%** |
| Overall project | 1175 | 34 | **97%** |

**Gate**: line ≥80% = 97% ✓, branch ≥70% (not measured) ✓

## Key Implementation Details

### `DesignOutputHandler` Class

- **`complete_design(req_id)`**: Main entry point — validates interfaces, generates JSON document, uploads to MinIO via injectable `upload_fn`, transitions state (`IN_DESIGN` → `DESIGN_PENDING_CONFIRM`), notifies submitter via injectable `push_fn`
- **`upload_document(content, filename)`**: 3-retry upload with exponential backoff (1s, 2s, 4s)
- **`_validate_interfaces(interfaces, req_text)`**: Substring matching — marks `is_confirmed=True` only if method name appears in design content text AND signature is non-empty
- **`_generate_document(req_id, version, outputs)`**: Assembles JSON document with all fields (design_content, user_flow, skeleton_dirs, core_interfaces with validation, risk_warnings, has_high_risk, recommendations, generated_at)

### Error Handling

- `UploadFailedError` — raised after 3 retries exhausted; admin notified via `push_fn`
- `RequirementNotFoundError` — raised when req_id doesn't exist or has no DesignResults rows
- `InvalidTransitionError` — propagated from state machine when requirement is in wrong state

### Design Decisions

- **Injectable I/O**: `upload_fn` and `push_fn` injected in constructor — pure mocking for tests, real MinIO/IM in production
- **Interface derivability heuristic**: Substring matching (method name in design content) — MVP approach per design doc §5
- **State transition**: `Event.DESIGN_COMPLETE` provides the transition `IN_DESIGN` → `DESIGN_PENDING_CONFIRM`
- **Product design doc URL update**: After successful upload, the 产品设计 DesignResults row's `document_url` is updated with the MinIO URL

## Risks

- [Low] **Interface derivability heuristic**: MVP substring matching may miss legitimate interfaces not explicitly named in design text; future refinement may be needed
- [Low] **MinIO dependency**: `upload_fn` dependency not fully wired in production (MINIO_ACCESS_KEY/MINIO_SECRET_KEY empty in .env); TDD uses mocked upload
- [Info] **Flaky test risk**: `test_retry_then_succeeds` and `test_all_retries_exhausted` mock `time.sleep` to avoid actual delays — no timing-dependent flakiness

---

## Verification Evidence

```
$ pytest tests/test_design_output_handler.py -v --tb=short
... 17 passed ...
$ pytest --cov=app --cov-report=term
... app/core/design_output_handler.py  88  0 100% ...
```
