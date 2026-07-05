# Test Case Document: 状态机引擎 (Feature #7)

**Feature ID**: 7
**Related Requirements**: FR-020
**Date**: 2026-07-06
**Standard**: ISO/IEC/IEEE 29119-3

## Summary

| Category | Count |
|----------|-------|
| FUNC | 12 |
| BNDRY | 5 |
| SEC | 0 |
| PERF | 1 |
| UI | 0 |
| **Total** | **18** |

## Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 18 |
| Passed | 18 |
| Failed | 0 |
| Pending | 0 |

## Manual Test Case Summary

No manual test cases — all cases are automated.

---

## Test Cases

### ST-FUNC-007-001: REVIEW_APPROVED → IN_DESIGN 自动流转

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-001 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 |
| **Feature Design Row** | Test A |

**Preconditions**: Requirement exists in REVIEW_APPROVED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_PASS)` | Returns `Status.IN_DESIGN` |

**Verification Points**: Auto-transition triggered correctly after review approval.

---

### ST-FUNC-007-002: DESIGN_CONFIRMED → IN_IMPLEMENTATION 自动流转

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-002 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 |
| **Feature Design Row** | Test B |

**Preconditions**: Requirement exists in DESIGN_CONFIRMED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.DESIGN_CONFIRM)` | Returns `Status.IN_IMPLEMENTATION` |

**Verification Points**: Auto-transition triggered after design confirmation.

---

### ST-FUNC-007-003: IMPL_APPROVED → DELIVERED 自动流转

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-003 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 |
| **Feature Design Row** | Test C |

**Preconditions**: Requirement exists in IMPL_APPROVED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.IMPL_CONFIRM)` | Returns `Status.DELIVERED` |

**Verification Points**: Auto-transition triggered after implementation approval.

---

### ST-FUNC-007-004: 并发隔离 — 多需求独立流转

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-004 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-2 |
| **Feature Design Row** | Test D |

**Preconditions**: Two requirements exist in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_PASS)` | Returns `Status.REVIEW_APPROVED` |
| 2 | Call `StateMachine.transition("REQ-20260705-002", Event.REVIEW_PASS)` | Returns `Status.REVIEW_APPROVED` |
| 3 | Verify both requirements have independent statuses | Both are REVIEW_APPROVED |

**Verification Points**: Concurrent transitions on different requirements do not interfere.

---

### ST-FUNC-007-005: 持久化恢复 — 中断后从最后状态恢复

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-005 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-3 |
| **Feature Design Row** | Test E |

**Preconditions**: Requirement exists in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_PASS)` | Returns `Status.REVIEW_APPROVED` |
| 2 | Create new session (simulate restart) | New session created |
| 3 | Call `StateMachine.get_status("REQ-20260705-001")` on new session | Returns `Status.REVIEW_APPROVED` |

**Verification Points**: Status persisted to SQLite and recoverable after session restart.

---

### ST-FUNC-007-006: transition 返回正确状态 + StatusHistory 记录

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-006 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 (interface contract) |
| **Feature Design Row** | Test F |

**Preconditions**: Requirement exists in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_PASS, "user1")` | Returns `Status.REVIEW_APPROVED` |
| 2 | Query `StatusHistory` table for the requirement | 1 row found |
| 3 | Verify `from_status` = "PENDING_REVIEW" | True |
| 4 | Verify `to_status` = "REVIEW_APPROVED" | True |
| 5 | Verify `trigger_event` = "REVIEW_PASS" | True |
| 6 | Verify `trigger_user` = "user1" | True |

**Verification Points**: StatusHistory correctly records all transition details.

---

### ST-FUNC-007-007: DELIVERED + REVIEW_PASS → InvalidTransitionError

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-007 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-4 |
| **Feature Design Row** | Test G |

**Preconditions**: Requirement exists in DELIVERED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_PASS)` | Raises `InvalidTransitionError` |

**Verification Points**: Invalid transition from terminal state is correctly rejected.

---

### ST-FUNC-007-008: REJECTED + DESIGN_CONFIRM → InvalidTransitionError

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-008 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-4 |
| **Feature Design Row** | Test H |

**Preconditions**: Requirement exists in REJECTED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.DESIGN_CONFIRM)` | Raises `InvalidTransitionError` |

**Verification Points**: Terminal state REJECTED correctly blocks further transitions.

---

### ST-FUNC-007-009: 不存在的需求 → RequirementNotFoundError

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-009 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-4 |
| **Feature Design Row** | Test I |

**Preconditions**: No requirement with ID "NONEXISTENT-001" exists.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("NONEXISTENT-001", Event.SUBMIT)` | Raises `RequirementNotFoundError` |

**Verification Points**: Missing requirement correctly raises error.

---

### ST-FUNC-007-010: PENDING_REVIEW + REVIEW_REJECT → PENDING_ARBITRATION

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-010 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 |
| **Feature Design Row** | Test M |

**Preconditions**: Requirement exists in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_REJECT)` | Returns `Status.PENDING_ARBITRATION` |

**Verification Points**: Review rejection correctly transitions to arbitration state.

---

### ST-FUNC-007-011: DESIGN_REJECTED + DESIGN_RETRY → IN_DESIGN

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-011 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 |
| **Feature Design Row** | Test N |

**Preconditions**: Requirement exists in DESIGN_REJECTED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.DESIGN_RETRY)` | Returns `Status.IN_DESIGN` |

**Verification Points**: Design retry correctly loops back to design phase.

---

### ST-FUNC-007-012: 空 trigger_user 被接受（系统自动流转）

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-007-012 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 (interface contract) |
| **Feature Design Row** | Test S |

**Preconditions**: Requirement exists in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.REVIEW_PASS, "")` | Returns `Status.REVIEW_APPROVED` |

**Verification Points**: Empty string trigger_user accepted for system auto-transitions.

---

### ST-BNDRY-007-001: TIMEOUT 第3次循环 — 状态不变

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-007-001 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 (boundary) |
| **Feature Design Row** | Test J |

**Preconditions**: Requirement exists in PENDING_ARBITRATION status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition("REQ-20260705-001", Event.TIMEOUT)` 3 times | No exception raised |
| 2 | Call `StateMachine.get_status("REQ-20260705-001")` | Returns `Status.PENDING_ARBITRATION` |

**Verification Points**: TIMEOUT event loops back to same state without error.

---

### ST-BNDRY-007-002: DESIGN_RETRY 第4次 — TERMINATED

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-007-002 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 (boundary) |
| **Feature Design Row** | Test K |

**Preconditions**: Requirement exists in DESIGN_REJECTED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Perform 3 retry cycles (DESIGN_RETRY → DESIGN_COMPLETE → DESIGN_REJECT) | All succeed |
| 2 | Call `StateMachine.transition("REQ-20260705-001", Event.DESIGN_RETRY)` (4th) | Returns `Status.TERMINATED` |

**Verification Points**: Max retry limit (3) enforced, 4th retry terminates.

---

### ST-BNDRY-007-003: IMPL_RETRY 第4次 — TERMINATED

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-007-003 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-1 (boundary) |
| **Feature Design Row** | Test L |

**Preconditions**: Requirement exists in IMPL_REJECTED status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Perform 3 retry cycles (IMPL_RETRY → IMPL_COMPLETE → IMPL_REJECT) | All succeed |
| 2 | Call `StateMachine.transition("REQ-20260705-001", Event.IMPL_RETRY)` (4th) | Returns `Status.TERMINATED` |

**Verification Points**: Max retry limit (3) enforced for implementation, 4th retry terminates.

---

### ST-BNDRY-007-004: None req_id → RequirementNotFoundError

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-007-004 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 AC-4 (boundary) |
| **Feature Design Row** | Test O |

**Preconditions**: StateMachine instantiated.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.transition(None, Event.SUBMIT)` | Raises `RequirementNotFoundError` |

**Verification Points**: None req_id correctly rejected.

---

### ST-BNDRY-007-005: can_transition 方法验证

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-007-005 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-020 (interface contract) |
| **Feature Design Row** | N/A |

**Preconditions**: Requirement exists in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Call `StateMachine.can_transition("REQ-20260705-001", Event.REVIEW_PASS)` | Returns `True` |
| 2 | Call `StateMachine.can_transition("REQ-20260705-001", Event.IMPL_CONFIRM)` | Returns `False` |

**Verification Points**: can_transition correctly reports valid/invalid transitions.

---

### PERF-007-001: 5并发流转无状态串扰

| Field | Value |
|-------|-------|
| **Case ID** | PERF-007-001 |
| **Category** | PERF |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | NFR-009 |
| **Feature Design Row** | Test R |

**Preconditions**: 5 requirements exist in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Execute 5 concurrent transitions on 5 different requirements | All return `Status.REVIEW_APPROVED` |
| 2 | Verify all 5 requirements have status REVIEW_APPROVED | True |
| 3 | Verify no cross-requirement state corruption | True |

**Verification Points**: Concurrent transitions do not cause state corruption.

---

## Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-007-001 | FR-020 AC-1 | Test A | test_auto_transition_to_in_design | PASS |
| ST-FUNC-007-002 | FR-020 AC-1 | Test B | test_auto_transition_to_in_implementation | PASS |
| ST-FUNC-007-003 | FR-020 AC-1 | Test C | test_auto_transition_to_delivered | PASS |
| ST-FUNC-007-004 | FR-020 AC-2 | Test D | test_concurrent_transitions_independent | PASS |
| ST-FUNC-007-005 | FR-020 AC-3 | Test E | test_persistence_recovery | PASS |
| ST-FUNC-007-006 | FR-020 AC-1 | Test F | test_transition_returns_status_and_history | PASS |
| ST-FUNC-007-007 | FR-020 AC-4 | Test G | test_invalid_transition_delivered | PASS |
| ST-FUNC-007-008 | FR-020 AC-4 | Test H | test_invalid_transition_rejected | PASS |
| ST-FUNC-007-009 | FR-020 AC-4 | Test I | test_requirement_not_found | PASS |
| ST-FUNC-007-010 | FR-020 AC-1 | Test M | test_review_reject_to_arbitration | PASS |
| ST-FUNC-007-011 | FR-020 AC-1 | Test N | test_design_retry_to_in_design | PASS |
| ST-FUNC-007-012 | FR-020 AC-1 | Test S | test_empty_trigger_user_accepted | PASS |
| ST-BNDRY-007-001 | FR-020 AC-1 | Test J | test_timeout_loop_third_time | PASS |
| ST-BNDRY-007-002 | FR-020 AC-1 | Test K | test_design_retry_max_exceeded | PASS |
| ST-BNDRY-007-003 | FR-020 AC-1 | Test L | test_impl_retry_max_exceeded | PASS |
| ST-BNDRY-007-004 | FR-020 AC-4 | Test O | test_none_req_id | PASS |
| ST-BNDRY-007-005 | FR-020 | N/A | test_can_transition_valid, test_can_transition_invalid, test_save_state, test_load_state_not_found | PASS |
| PERF-007-001 | NFR-009 | Test R | test_concurrent_transitions_no_corruption | PASS |
