# Feature-Level ST Test Case Document: IM Webhook 接入 (F003)

**Feature ID**: 3
**Feature Title**: IM Webhook 接入
**Related Requirements**: FR-001
**Date**: 2026-07-05
**Standard**: ISO/IEC/IEEE 29119-3
**Design Reference**: docs/features/2026-07-05-F003-im-webhook.md

**Specification resolutions applied from Feature Design Clarification Addendum.**
- No clarifications required — all specifications were unambiguous.

---

## 1. Summary Table

| Category | Abbreviation | Count |
|----------|-------------|-------|
| Functional | FUNC | 6 |
| Boundary | BNDRY | 3 |
| UI | UI | 0 |
| Security | SEC | 2 |
| Performance | PERF | 1 |
| **Total** | | **12** |

---

## 2. Test Cases

---

### ST-FUNC-003-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-003-001 |
| **Test Objective** | Requirement message recognized and processed |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-001 AC-1, Test Inventory Row A |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with valid payload containing `content="加一个登录页"` and `message_type=text` | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "需求已提交" |

---

### ST-FUNC-003-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-003-002 |
| **Test Objective** | Command message recognized and routed |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-001 AC-2, Test Inventory Row B |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with valid payload containing `content="确认 REQ-20260704-001"` and `message_type=text` | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "指令已执行" |

---

### ST-FUNC-003-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-003-003 |
| **Test Objective** | Unsupported message type rejected with appropriate message |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-001 AC-3, Test Inventory Row C |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with payload containing `content=null` and `message_type="image"` | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "本轮仅支持文本需求与指令" |

---

### ST-FUNC-003-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-003-004 |
| **Test Objective** | Downstream failure triggers retry and error response |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-001 AC-4, Test Inventory Row D |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible; mock downstream failure (DB connection error) |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with valid payload; mock `MessageRouter.route` to raise `ConnectionError` | HTTP 200 |
| 2 | Parse response JSON | `status` equals "error", `message` contains "处理失败" |

---

### ST-FUNC-003-005

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-003-005 |
| **Test Objective** | Valid Webhook payload matches C-001 contract schema |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §4.2 C-001, Test Inventory Row J |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with valid IM Webhook Payload JSON | HTTP 200 |
| 2 | Parse response JSON | JSON contains "status" and "message" fields (C-001 schema) |

---

### ST-FUNC-003-006

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-003-006 |
| **Test Objective** | Malformed JSON payload rejected with appropriate error |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §4.2 C-001, Test Inventory Row K |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with invalid JSON body (`content-type: application/json`) | HTTP 422 |
| 2 | Response body contains validation error details | FastAPI validation error schema |

---

### ST-BNDRY-003-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-003-001 |
| **Test Objective** | Empty content string treated as unsupported message |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Algorithm boundary, Test Inventory Row E |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with payload containing `content=""` (empty string) | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "本轮仅支持文本需求与指令" |

---

### ST-BNDRY-003-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-003-002 |
| **Test Objective** | Maximum length content processed without error |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Algorithm boundary, Test Inventory Row F |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with payload containing `content` of 10,000 characters | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "需求已提交" |

---

### ST-BNDRY-003-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-003-003 |
| **Test Objective** | Missing required field triggers validation error |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Algorithm boundary, Test Inventory Row G |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with payload missing `sender_id` field | HTTP 400 |
| 2 | Response contains error message indicating missing field | "missing required field" appears in response |

---

### ST-SEC-003-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-SEC-003-001 |
| **Test Objective** | SQL injection attempt stored as literal string |
| **Category** | SEC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Interface Contract, Test Inventory Row H |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with payload containing `content="'; DROP TABLE requirements; --"` | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "需求已提交" |
| 3 | Verify content stored as literal string (no SQL execution) | Database unchanged; requirement created with literal content |

---

### ST-SEC-003-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-SEC-003-002 |
| **Test Objective** | XSS payload stored as literal string |
| **Category** | SEC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Design §Interface Contract, Test Inventory Row I |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/webhook/im/feishu` with payload containing `content="<script>alert('xss')</script>"` | HTTP 200 |
| 2 | Parse response JSON | `status` equals "ok", `message` contains "需求已提交" |
| 3 | Verify content stored as literal string (no script execution) | Requirement created with literal content |

---

### ST-PERF-003-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-PERF-003-001 |
| **Test Objective** | Concurrent webhook requests meet P95 latency threshold |
| **Category** | PERF |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | NFR-001, Test Inventory Row L |
| **Preconditions** | FastAPI server running; IM platform configured as 'feishu'; Webhook endpoint accessible |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Send 100 concurrent POST requests to `/webhook/im/feishu` with valid payloads over 60s ramp | All requests complete |
| 2 | Calculate P95 response time | P95 < 5 seconds |

---

## 3. Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-003-001 | FR-001 AC-1 | A | `test_handle_webhook_requirement_message_recognized` | PASS |
| ST-FUNC-003-002 | FR-001 AC-2 | B | `test_handle_webhook_command_message_recognized` | PASS |
| ST-FUNC-003-003 | FR-001 AC-3 | C | `test_handle_webhook_unsupported_message_type` | PASS |
| ST-FUNC-003-004 | FR-001 AC-4 | D | `test_handle_webhook_downstream_failure_retry` | PASS |
| ST-FUNC-003-005 | FR-001 (C-001) | J | `test_handle_webhook_valid_c001_schema` | PASS |
| ST-FUNC-003-006 | FR-001 (C-001) | K | `test_handle_webhook_malformed_json` | PASS |
| ST-BNDRY-003-001 | FR-001 AC-3 | E | `test_handle_webhook_empty_content` | PASS |
| ST-BNDRY-003-002 | FR-001 AC-1 | F | `test_handle_webhook_max_length_content` | PASS |
| ST-BNDRY-003-003 | FR-001 (payload) | G | `test_handle_webhook_missing_required_field` | PASS |
| ST-SEC-003-001 | FR-001 (security) | H | `test_handle_webhook_sql_injection_content` | PASS |
| ST-SEC-003-002 | FR-001 (security) | I | `test_handle_webhook_xss_content` | PASS |
| ST-PERF-003-001 | NFR-001 | L | `test_handle_webhook_concurrent_performance` | PASS |

---

## 4. Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 12 |
| Passed | 12 |
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