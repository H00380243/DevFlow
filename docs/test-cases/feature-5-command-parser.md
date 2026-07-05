# Feature-Level ST Test Case Document: 状态变更指令系统 (F005)

**Feature ID**: 5
**Feature Title**: 状态变更指令系统
**Related Requirements**: FR-004a
**Date**: 2026-07-05
**Standard**: ISO/IEC/IEEE 29119-3
**Design Reference**: docs/features/2026-07-05-F005-command-parser.md

**Specification resolutions applied from Feature Design Clarification Addendum.**
- No clarifications required — all specifications were unambiguous.

---

## 1. Summary Table

| Category | Abbreviation | Count |
|----------|-------------|-------|
| Functional | FUNC | 7 |
| Boundary | BNDRY | 6 |
| Security | SEC | 2 |
| **Total** | | **15** |

---

## 2. Test Cases

---

### ST-FUNC-005-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-001 |
| **Test Objective** | Parse valid confirm command and return ConfirmCommand |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-1, Test Inventory Row A |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Instantiate `CommandParser()` | Parser object created |
| 2 | Call `parser.parse("确认 REQ-20260705-001")` | Returns `ConfirmCommand` |
| 3 | Assert `result.command_type == "confirm"` | Command type is confirm |
| 4 | Assert `result.requirement_id == "REQ-20260705-001"` | Requirement ID extracted correctly |

---

### ST-FUNC-005-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-002 |
| **Test Objective** | Parse valid reject command with reason and return RejectCommand |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-2, Test Inventory Row B |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Instantiate `CommandParser()` | Parser object created |
| 2 | Call `parser.parse("驳回 REQ-20260705-001 逻辑不清")` | Returns `RejectCommand` |
| 3 | Assert `result.command_type == "reject"` | Command type is reject |
| 4 | Assert `result.requirement_id == "REQ-20260705-001"` | Requirement ID extracted |
| 5 | Assert `result.reason == "逻辑不清"` | Reason extracted correctly |

---

### ST-FUNC-005-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-003 |
| **Test Objective** | Confirm command executed successfully via CommandExecutor |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-1, Test Inventory Row A |
| **Preconditions** | app.core.command_executor module importable; mock DB with submitter_id matching sender |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB: submitter_id="user1", requirement exists | DB configured |
| 2 | Call `CommandExecutor().execute("user1", "确认 REQ-20260705-001", mock_db)` | Returns `CommandResult` |
| 3 | Assert `result.status == "ok"` | Status is ok |
| 4 | Assert `"已确认 REQ-20260705-001" in result.message` | Success message present |

---

### ST-FUNC-005-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-004 |
| **Test Objective** | Reject command with reason executed successfully via CommandExecutor |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-2, Test Inventory Row B |
| **Preconditions** | app.core.command_executor module importable; mock DB with submitter_id matching sender |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB: submitter_id="user1", requirement exists | DB configured |
| 2 | Call `CommandExecutor().execute("user1", "驳回 REQ-20260705-001 逻辑不清", mock_db)` | Returns `CommandResult` |
| 3 | Assert `result.status == "ok"` | Status is ok |
| 4 | Assert `"已驳回 REQ-20260705-001 逻辑不清" in result.message` | Success message with reason |

---

### ST-FUNC-005-005

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-005 |
| **Test Objective** | Non-submitter gets permission denied error |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-3, Test Inventory Row C |
| **Preconditions** | app.core.command_executor module importable; mock DB with submitter_id="user1" |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB: submitter_id="user1" | DB configured |
| 2 | Call `CommandExecutor().execute("user2", "确认 REQ-20260705-001", mock_db)` | Returns `CommandResult` |
| 3 | Assert `result.status == "error"` | Status is error |
| 4 | Assert `"无权限" in result.message` | Permission denied message |

---

### ST-FUNC-005-006

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-006 |
| **Test Objective** | Non-existent requirement returns error |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-4, Test Inventory Row D |
| **Preconditions** | app.core.command_executor module importable; mock DB returns None for requirement |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB: submitter matches but requirement doesn't exist | DB configured |
| 2 | Call `CommandExecutor().execute("user1", "确认 REQ-99999999-999", mock_db)` | Returns `CommandResult` |
| 3 | Assert `result.status == "error"` | Status is error |
| 4 | Assert `"不存在" in result.message` | Not-found message |

---

### ST-FUNC-005-007

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-005-007 |
| **Test Objective** | Invalid command text returns error with format hint |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-4, Test Inventory Row O |
| **Preconditions** | app.core.command_executor module importable |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandExecutor().execute("user1", "invalid text", mock_db)` | Returns `CommandResult` |
| 2 | Assert `result.status == "error"` | Status is error |
| 3 | Assert `"正确格式" in result.message` | Format hint present |

---

### ST-BNDRY-005-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-005-001 |
| **Test Objective** | Null input raises CommandParseError |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row E |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse(None)` | Raises `CommandParseError` |
| 2 | Assert error message contains "指令不能为空" | Correct error message |

---

### ST-BNDRY-005-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-005-002 |
| **Test Objective** | Empty string input raises CommandParseError |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row F |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("")` | Raises `CommandParseError` |
| 2 | Assert error message contains "指令不能为空" | Correct error message |

---

### ST-BNDRY-005-003

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-005-003 |
| **Test Objective** | Leading/trailing whitespace is stripped correctly |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row G |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("  确认 REQ-20260705-001  ")` | Returns `ConfirmCommand` |
| 2 | Assert `result.requirement_id == "REQ-20260705-001"` | Whitespace stripped, ID correct |

---

### ST-BNDRY-005-004

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-005-004 |
| **Test Objective** | Missing space after command prefix raises error |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row H |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("确认REQ-20260705-001")` | Raises `CommandParseError` |
| 2 | Assert error message contains "正确格式" | Correct format hint |

---

### ST-BNDRY-005-005

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-005-005 |
| **Test Objective** | Trailing space only after command prefix raises error |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row I |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("确认 ")` | Raises `CommandParseError` |
| 2 | Assert error message contains "正确格式" | Correct format hint |

---

### ST-BNDRY-005-006

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-005-006 |
| **Test Objective** | Reject without reason returns empty reason string |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row J |
| **Preconditions** | app.core.command_parser module importable |
| **Priority** | Medium |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("驳回 REQ-20260705-001")` | Returns `RejectCommand` |
| 2 | Assert `result.requirement_id == "REQ-20260705-001"` | ID extracted |
| 3 | Assert `result.reason == ""` | Empty reason, no crash |

---

### ST-SEC-005-001

| Field | Value |
|-------|-------|
| **Case ID** | ST-SEC-005-001 |
| **Test Objective** | Reject command also checks permission (non-submitter rejected) |
| **Category** | SEC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004a AC-3, Test Inventory Row M |
| **Preconditions** | app.core.command_executor module importable; mock DB with submitter_id="user1" |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB: submitter_id="user1" | DB configured |
| 2 | Call `CommandExecutor().execute("user2", "驳回 REQ-20260705-001 意见", mock_db)` | Returns `CommandResult` |
| 3 | Assert `result.status == "error"` | Status is error |
| 4 | Assert `"无权限" in result.message` | Permission denied message |

---

### ST-SEC-005-002

| Field | Value |
|-------|-------|
| **Case ID** | ST-SEC-005-002 |
| **Test Objective** | Permission check for non-existent requirement returns error |
| **Category** | SEC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | Test Inventory Row N |
| **Preconditions** | app.core.command_executor module importable; mock DB returns None for requirement |
| **Priority** | High |

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Mock DB: requirement doesn't exist (first query returns None) | DB configured |
| 2 | Call `CommandExecutor().execute("user1", "确认 REQ-99999999-999", mock_db)` | Returns `CommandResult` |
| 3 | Assert `result.status == "error"` | Status is error |
| 4 | Assert `"无权限" in result.message` or `"不存在" in result.message` | Error message present |

---

## 3. Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-005-001 | FR-004a AC-1 | A | `TestParseConfirmHappyPath::test_parse_confirm_returns_confirm_command` | PASS |
| ST-FUNC-005-002 | FR-004a AC-2 | B | `TestParseRejectHappyPath::test_parse_reject_with_reason` | PASS |
| ST-FUNC-005-003 | FR-004a AC-1 | A | `TestExecuteConfirmHappyPath::test_execute_confirm_ok` | PASS |
| ST-FUNC-005-004 | FR-004a AC-2 | B | `TestExecuteRejectHappyPath::test_execute_reject_with_reason` | PASS |
| ST-FUNC-005-005 | FR-004a AC-3 | C | `TestExecutePermissionDenied::test_execute_permission_denied` | PASS |
| ST-FUNC-005-006 | FR-004a AC-4 | D | `TestExecuteRequirementNotFound::test_execute_requirement_not_found` | PASS |
| ST-FUNC-005-007 | FR-004a AC-4 | O | `TestExecuteParseError::test_execute_parse_error` | PASS |
| ST-BNDRY-005-001 | FR-004a AC-4 | E | `TestParseNullInput::test_parse_none_raises` | PASS |
| ST-BNDRY-005-002 | FR-004a AC-4 | F | `TestParseEmptyInput::test_parse_empty_string_raises` | PASS |
| ST-BNDRY-005-003 | FR-004a AC-4 | G | `TestParseWhitespaceStripping::test_parse_with_surrounding_whitespace` | PASS |
| ST-BNDRY-005-004 | FR-004a AC-4 | H | `TestParseMissingSpaceAfterConfirm::test_parse_no_space_after_confirm` | PASS |
| ST-BNDRY-005-005 | FR-004a AC-4 | I | `TestParseTrailingSpaceOnlyAfterConfirm::test_parse_trailing_space_after_confirm` | PASS |
| ST-BNDRY-005-006 | FR-004a AC-4 | J | `TestParseRejectWithoutReason::test_parse_reject_no_reason` | PASS |
| ST-SEC-005-001 | FR-004a AC-3 | M | `TestExecuteRejectPermissionDenied::test_execute_reject_permission_denied` | PASS |
| ST-SEC-005-002 | FR-004a AC-4 | N | `TestExecutePermissionCheckForNonExistentRequirement::test_permission_check_nonexistent_req` | PASS |

---

## 4. Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 15 |
| Passed | 15 |
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
