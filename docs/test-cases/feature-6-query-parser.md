# Test Case Document: 查询指令系统 (Feature #F006)

**Feature ID**: 6
**Related Requirements**: FR-004b
**Date**: 2026-07-05
**Standard**: ISO/IEC/IEEE 29119-3

## Summary

| Category | Count |
|----------|-------|
| FUNC | 7 |
| BNDRY | 8 |
| SEC | 0 |
| PERF | 0 |
| UI | 0 |
| **Total** | **15** |

## Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 15 |
| Passed | 15 |
| Failed | 0 |
| Pending | 0 |

## Manual Test Case Summary

No manual test cases — all cases are automated.

---

## Test Cases

### ST-FUNC-006-001: 进度命令解析 — Happy Path

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-001 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-1 |
| **Feature Design Row** | Test A |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("进度 REQ-20260705-001")` | Returns `ProgressCommand` instance |
| 2 | Assert `result.requirement_id` | Equals `"REQ-20260705-001"` |

**Verification Points**: CommandParser correctly identifies "进度 " prefix and extracts REQ ID.

---

### ST-FUNC-006-002: 我的列表命令解析 — Happy Path

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-002 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-2 |
| **Feature Design Row** | Test B |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("我的列表")` | Returns `ListCommand` instance |

**Verification Points**: CommandParser correctly matches exact string "我的列表".

---

### ST-FUNC-006-003: 进度命令执行 — Full Path with DB

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-003 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-1 (full path) |
| **Feature Design Row** | Test C |

**Preconditions**: Mock DB returns a row with current_stage="评审", current_status="待确认".

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandExecutor().execute("U001", "进度 REQ-20260705-001", mock_db)` | Returns `CommandResult` |
| 2 | Assert `result.status` | Equals `"ok"` |
| 3 | Assert `result.message` contains "阶段=评审" | True |
| 4 | Assert `result.message` contains "状态=待确认" | True |
| 5 | Assert `result.message` contains "REQ-20260705-001" | True |

**Verification Points**: CommandExecutor routes ProgressCommand to QueryExecutor; DB query returns formatted stage/status.

---

### ST-FUNC-006-004: 我的列表命令执行 — Full Path with DB

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-004 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-2 (full path) |
| **Feature Design Row** | Test D |

**Preconditions**: Mock DB returns 2 rows for submitter U001.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandExecutor().execute("U001", "我的列表", mock_db)` | Returns `CommandResult` |
| 2 | Assert `result.status` | Equals `"ok"` |
| 3 | Assert `result.message` contains "您的需求清单" | True |
| 4 | Assert `result.message` contains "REQ-20260705-001" | True |
| 5 | Assert `result.message` contains "REQ-20260705-002" | True |

**Verification Points**: CommandExecutor routes ListCommand to QueryExecutor; DB query returns formatted list.

---

### ST-FUNC-006-005: 进度命令 — 需求不存在

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-005 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-3 |
| **Feature Design Row** | Test E |

**Preconditions**: Mock DB returns None for the query.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandExecutor().execute("U001", "进度 REQ-20260705-999", mock_db)` | Returns `CommandResult` |
| 2 | Assert `result.status` | Equals `"error"` |
| 3 | Assert `result.message` contains "REQ-20260705-999" | True |
| 4 | Assert `result.message` contains "不存在" | True |

**Verification Points**: QueryExecutor checks for None result and returns error message.

---

### ST-FUNC-006-006: 进度命令 — 缺少 REQ ID

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-006 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 |
| **Feature Design Row** | Test F |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("进度 ")` | Raises `CommandParseError` |
| 2 | Assert exception message matches "正确格式: 进度 REQ-YYYYMMDD-NNN" | True |

**Verification Points**: Parser validates REQ ID presence after "进度 " prefix.

---

### ST-FUNC-006-007: 未识别的指令前缀

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-006-007 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 |
| **Feature Design Row** | Test G |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("查询 REQ-20260705-001")` | Raises `CommandParseError` |
| 2 | Assert exception message matches "正确格式" | True |

**Verification Points**: Parser rejects unrecognized command prefixes.

---

### ST-BNDRY-006-001: None 输入

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-001 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 (boundary) |
| **Feature Design Row** | Test H |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse(None)` | Raises `CommandParseError` |
| 2 | Assert exception message matches "指令不能为空" | True |

**Verification Points**: Parser handles None input gracefully.

---

### ST-BNDRY-006-002: 空字符串输入

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-002 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 (boundary) |
| **Feature Design Row** | Test I |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("")` | Raises `CommandParseError` |
| 2 | Assert exception message matches "指令不能为空" | True |

**Verification Points**: Parser handles empty string input.

---

### ST-BNDRY-006-003: 纯空白输入

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-003 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 (boundary) |
| **Feature Design Row** | Test J |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("   ")` | Raises `CommandParseError` |
| 2 | Assert exception message matches "指令不能为空" | True |

**Verification Points**: Parser strips whitespace before checking emptiness.

---

### ST-BNDRY-006-004: 进度命令双空格分隔

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-004 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-1 (boundary) |
| **Feature Design Row** | Test K |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("进度  REQ-20260705-001")` | Returns `ProgressCommand` |
| 2 | Assert `result.requirement_id` | Equals `"REQ-20260705-001"` |

**Verification Points**: Parser handles double-space separator after "进度".

---

### ST-BNDRY-006-005: 进度命令前后空白

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-005 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-1 (boundary) |
| **Feature Design Row** | Test L |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("  进度 REQ-20260705-001  ")` | Returns `ProgressCommand` |
| 2 | Assert `result.requirement_id` | Equals `"REQ-20260705-001"` |

**Verification Points**: Parser strips leading/trailing whitespace.

---

### ST-BNDRY-006-006: 我的列表附加文字

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-006 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 (boundary) |
| **Feature Design Row** | Test M |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("我的列表 请查看")` | Raises `CommandParseError` |

**Verification Points**: "我的列表" requires exact match — extra text is rejected.

---

### ST-BNDRY-006-007: 我的列表空结果

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-007 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-2 (boundary) |
| **Feature Design Row** | Test N |

**Preconditions**: Mock DB returns empty list for submitter.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandExecutor().execute("U001", "我的列表", mock_db)` | Returns `CommandResult` |
| 2 | Assert `result.status` | Equals `"ok"` |
| 3 | Assert `result.message` contains "暂无需求记录" | True |

**Verification Points**: Empty list returns ok status with friendly message, not error.

---

### ST-BNDRY-006-008: 进度命令无效 REQ ID 格式

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-006-008 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-004b AC-4 (boundary) |
| **Feature Design Row** | Test O |

**Preconditions**: CommandParser instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `CommandParser().parse("进度 REQ-invalid")` | Raises `CommandParseError` |
| 2 | Assert exception message matches "正确格式: 进度 REQ-YYYYMMDD-NNN" | True |

**Verification Points**: Parser validates REQ ID format via REQ_ID_PATTERN regex.

---

## Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-006-001 | FR-004b AC-1 | Test A | test_parse_progress_returns_progress_command | PASS |
| ST-FUNC-006-002 | FR-004b AC-2 | Test B | test_parse_list_returns_list_command | PASS |
| ST-FUNC-006-003 | FR-004b AC-1 | Test C | test_execute_progress_ok | PASS |
| ST-FUNC-006-004 | FR-004b AC-2 | Test D | test_execute_list_ok | PASS |
| ST-FUNC-006-005 | FR-004b AC-3 | Test E | test_execute_progress_not_found | PASS |
| ST-FUNC-006-006 | FR-004b AC-4 | Test F | test_parse_progress_without_req_id | PASS |
| ST-FUNC-006-007 | FR-004b AC-4 | Test G | test_parse_unrecognized_prefix | PASS |
| ST-BNDRY-006-001 | FR-004b AC-4 | Test H | test_parse_none_raises | PASS |
| ST-BNDRY-006-002 | FR-004b AC-4 | Test I | test_parse_empty_string_raises | PASS |
| ST-BNDRY-006-003 | FR-004b AC-4 | Test J | test_parse_whitespace_only_raises | PASS |
| ST-BNDRY-006-004 | FR-004b AC-1 | Test K | test_parse_progress_double_space | PASS |
| ST-BNDRY-006-005 | FR-004b AC-1 | Test L | test_parse_progress_surrounding_whitespace | PASS |
| ST-BNDRY-006-006 | FR-004b AC-4 | Test M | test_parse_list_with_extra_text | PASS |
| ST-BNDRY-006-007 | FR-004b AC-2 | Test N | test_execute_list_empty | PASS |
| ST-BNDRY-006-008 | FR-004b AC-4 | Test O | test_parse_progress_invalid_req_id | PASS |
