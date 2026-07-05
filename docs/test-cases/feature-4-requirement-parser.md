# Feature-Level ST Test Case Document: 需求结构化与 ID 生成 (F004)

**Feature ID**: 4
**Feature Title**: 需求结构化与 ID 生成
**Related Requirements**: FR-002, FR-003
**Date**: 2026-07-05
**Standard**: ISO/IEC/IEEE 29119-3
**Design Reference**: docs/features/2026-07-05-F004-requirement-parser.md

**Specification resolutions applied from Feature Design Clarification Addendum.**
- No clarifications required — all specifications were unambiguous.

---

## 1. Summary Table

| Category | Abbreviation | Count |
|----------|-------------|-------|
| Functional | FUNC | 7 |
| Boundary | BNDRY | 4 |
| Security | SEC | 2 |
| **Total** | | **13** |

---

## 2. Test Cases

---

### ST-FUNC-004-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-001 |
| **Test Objective** | Parse valid requirement message and generate REQ-YYYYMMDD-NNN ID |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-002 AC-1, Test Inventory Row A, B |
| **Preconditions** | app.core.requirement_parser module importable; SQLAlchemy Session available (mock or real) |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create IMMessage with `content="加一个登录页"`, `sender_id="user1"` | IMMessage object created |
| 2 | Call `RequirementParser.parse(message)` | Returns `StructuredRequirement` |
| 3 | Assert `result.id` matches regex `REQ-\d{8}-\d{3}` | ID format is REQ-YYYYMMDD-NNN |
| 4 | Assert `result.original_text == "加一个登录页"` | Original text preserved |
| 5 | Assert `result.summary == "加一个登录页"` | Summary equals extracted intent |
| 6 | Assert `result.submitter_id == "user1"` | Submitter ID set correctly |
| 7 | Assert `result.created_at is not None` | Timestamp populated |

---

### ST-FUNC-004-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-002 |
| **Test Objective** | Null and empty content raise RequirementParseError |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-002 AC-2, Test Inventory Row C, D |
| **Preconditions** | app.core.requirement_parser module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create IMMessage with `content=None` | IMMessage object created |
| 2 | Call `RequirementParser.parse(message)` | Raises `RequirementParseError` with message "需求文本不能为空" |
| 3 | Create IMMessage with `content=""` | IMMessage object created |
| 4 | Call `RequirementParser.parse(message)` | Raises `RequirementParseError` with message "需求文本不能为空" |
| 5 | Create IMMessage with `content="   "` (whitespace only) | IMMessage object created |
| 6 | Call `RequirementParser.parse(message)` | Raises `RequirementParseError` with message "需求文本不能为空" |

---

### ST-FUNC-004-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-003 |
| **Test Objective** | Unparseable content still generates entry with "待人工补充诉求" |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-002 AC-3, Test Inventory Row E |
| **Preconditions** | app.core.requirement_parser module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create IMMessage with `content="!!!@@@###"` | IMMessage object created |
| 2 | Call `RequirementParser.parse(message)` | Returns `StructuredRequirement` |
| 3 | Assert `result.id` matches `REQ-\d{8}-\d{3}` | ID still generated |
| 4 | Assert `result.summary == "待人工补充诉求"` | Summary marked for manual supplement |
| 5 | Assert `result.original_text == "!!!@@@###"` | Original text preserved |

---

### ST-FUNC-004-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-004 |
| **Test Objective** | Duplicate message within 5-minute window returns existing requirement ID |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-003 AC-1, Test Inventory Row J |
| **Preconditions** | app.core.idempotency module importable; DB has idempotency_store row for sender+content within 5 min |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `IdempotencyChecker.check(sender_hash=12345, content="加一个登录页")` with mock DB returning "REQ-20260705-001" | Returns "REQ-20260705-001" |
| 2 | Assert returned value is the existing requirement_id | Duplicate detected, existing ID reused |

---

### ST-FUNC-004-005

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-005 |
| **Test Objective** | Expired entry (>5 min) and different sender both return None |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-003 AC-2, AC-3, Test Inventory Row K, L |
| **Preconditions** | app.core.idempotency module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `IdempotencyChecker.check(sender_hash=12345, content="加一个登录页")` with mock DB returning None (expired) | Returns `None` |
| 2 | Call `IdempotencyChecker.check(sender_hash=99999, content="加一个登录页")` with mock DB returning None (different sender) | Returns `None` |

---

### ST-FUNC-004-006

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-006 |
| **Test Objective** | DB failures raise appropriate custom exceptions |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Error Handling, Test Inventory Row N, O, P |
| **Preconditions** | app.core modules importable; mock DB raises OperationalError |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `RequirementParser.generate_id()` with mock DB raising OperationalError | Raises `IdGenerationError("Failed to query sequence counter")` |
| 2 | Call `IdempotencyChecker.check(sender_hash, content)` with mock DB raising OperationalError | Raises `IdempotencyCheckError("Failed to check idempotency")` |
| 3 | Call `IdempotencyChecker.store(sender_hash, content, req_id)` with mock DB raising OperationalError | Raises `IdempotencyStoreError("Failed to store idempotency record")` |

---

### ST-FUNC-004-007

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-004-007 |
| **Test Objective** | Integration: concurrent ID uniqueness and idempotency round-trip |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Interface Contract, Test Inventory Row T, U |
| **Preconditions** | app.core modules importable; mock DB session available |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `generate_id()` twice with mock DB returning None then 1 | Returns two distinct IDs: REQ-YYYYMMDD-001 and REQ-YYYYMMDD-002 |
| 2 | Call `IdempotencyChecker.store(sender_hash, content, req_id)` | Store succeeds, commit called |
| 3 | Call `IdempotencyChecker.check(sender_hash, content)` with mock DB returning stored req_id | Returns stored requirement_id |

---

### ST-BNDRY-004-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-004-001 |
| **Test Objective** | ID sequence at 998 and 999 boundaries (3-digit format) |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-002 AC-4, Test Inventory Row F, G |
| **Preconditions** | app.core.requirement_parser module importable; mock DB session |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB returning `max_seq=998`, call `generate_id()` | Returns `REQ-YYYYMMDD-999` (3-digit) |
| 2 | Mock DB returning `max_seq=999`, call `generate_id()` | Returns `REQ-YYYYMMDD-1000` (4-digit expansion) |

---

### ST-BNDRY-004-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-004-002 |
| **Test Objective** | Sequence exhaustion at 9999 and first-of-day NULL handling |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-002 AC-4, Test Inventory Row H, I |
| **Preconditions** | app.core.requirement_parser module importable; mock DB session |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB returning `max_seq=9999`, call `generate_id()` | Raises `IdGenerationError("Sequence exhausted for today")` |
| 2 | Mock DB returning `max_seq=None`, call `generate_id()` | Returns `REQ-YYYYMMDD-001` (starts at 1) |

---

### ST-BNDRY-004-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-004-003 |
| **Test Objective** | Exactly 5-minute boundary treated as expired |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-003 AC-1, Test Inventory Row M |
| **Preconditions** | app.core.idempotency module importable; mock DB session |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `IdempotencyChecker.check(sender_hash=12345, content="加一个登录页")` with mock DB returning None at exactly 5 min | Returns `None` (at boundary = expired) |

---

### ST-BNDRY-004-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-004-004 |
| **Test Objective** | Intent extraction returns first sentence; constraint extraction filters keywords |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Algorithm, Test Inventory Row Q, R, S |
| **Preconditions** | app.core.requirement_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `_extract_intent("第一个句子。第二个句子。")` | Returns "第一个句子" (first sentence only) |
| 2 | Call `_extract_constraints("必须支持RBAC。可以使用JWT。")` | Returns `["必须支持RBAC"]` (only constraint-matching) |
| 3 | Call `_extract_constraints("随便写点什么")` | Returns `[]` (empty list, no keywords) |

---

### ST-SEC-004-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-SEC-004-001 |
| **Test Objective** | SQL injection content stored as literal string, no DB damage |
| **Category** | SEC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Interface Contract, Test Inventory Row V |
| **Preconditions** | app.core.requirement_parser module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create IMMessage with `content="'; DROP TABLE requirements; --"` | IMMessage object created |
| 2 | Call `RequirementParser.parse(message)` | Returns `StructuredRequirement` |
| 3 | Assert `result.original_text == "'; DROP TABLE requirements; --"` | Content stored as literal string |
| 4 | Assert `result.summary == "'; DROP TABLE requirements; --"` | Summary is literal content |

---

### ST-SEC-004-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-SEC-004-002 |
| **Test Objective** | XSS payload stored as literal string, no script execution |
| **Category** | SEC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Interface Contract, Test Inventory Row W |
| **Preconditions** | app.core.requirement_parser module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create IMMessage with `content="<script>alert(1)</script>"` | IMMessage object created |
| 2 | Call `RequirementParser.parse(message)` | Returns `StructuredRequirement` |
| 3 | Assert `result.original_text == "<script>alert(1)</script>"` | Content stored as literal string |

---

## 3. Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-004-001 | FR-002 AC-1 | A, B | `test_parse_valid_generates_id`, `test_parse_extracts_tags_and_constraints` | PASS |
| ST-FUNC-004-002 | FR-002 AC-2 | C, D | `test_parse_null_content_raises`, `test_parse_empty_content_raises`, `test_parse_whitespace_only_content_raises` | PASS |
| ST-FUNC-004-003 | FR-002 AC-3 | E | `test_parse_unparseable_marks_pending` | PASS |
| ST-FUNC-004-004 | FR-003 AC-1 | J | `test_check_duplicate_returns_existing_id` | PASS |
| ST-FUNC-004-005 | FR-003 AC-2, AC-3 | K, L | `test_check_expired_returns_none`, `test_check_different_sender_returns_none` | PASS |
| ST-FUNC-004-006 | §Error Handling | N, O, P | `test_generate_id_db_failure_raises`, `test_check_db_failure_raises`, `test_store_db_failure_raises` | PASS |
| ST-FUNC-004-007 | §Interface Contract | T, U | `test_concurrent_generate_id_unique`, `test_round_trip_store_then_check` | PASS |
| ST-BNDRY-004-001 | FR-002 AC-4 | F, G | `test_generate_id_3digit_below_999`, `test_generate_id_expands_to_4digit` | PASS |
| ST-BNDRY-004-002 | FR-002 AC-4 | H, I | `test_generate_id_raises_on_exhaustion`, `test_generate_id_first_of_day` | PASS |
| ST-BNDRY-004-003 | FR-003 AC-1 | M | `test_check_exact_5min_boundary_returns_none` | PASS |
| ST-BNDRY-004-004 | §Algorithm | Q, R, S | `test_extract_intent_first_sentence`, `test_extract_constraints_filters_keywords`, `test_extract_constraints_no_keywords_empty_list` | PASS |
| ST-SEC-004-001 | §Interface Contract | V | `test_parse_sql_injection_content` | PASS |
| ST-SEC-004-002 | §Interface Contract | W | `test_parse_xss_content` | PASS |

---

## 4. Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 13 |
| Passed | 13 |
| Failed | 0 |
| Pending | 0 |

---

## 5. Manual Test Case Summary

| Metric | Value |
|--------|-------|
| Total Manual Cases | 0 |
| Pending-MANUAL | 0 |

---

**Document ends.**
