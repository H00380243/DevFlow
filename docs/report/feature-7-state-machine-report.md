# Feature Development Report: F007 — 状态机引擎

**Feature ID**: 7
**Feature Title**: 状态机引擎
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-06
**Git SHA**: `8779ae5`

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 7 |
| Title | 状态机引擎 |
| Category | core |
| Priority | high |
| Dependencies | F002 (数据模型与迁移) |
| UI | false |
| SRS Trace | FR-020 |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-020: 工作流状态机自动流转**
- EARS: When 上一节点完成，the system shall 自动触发下一节点任务并维护需求全生命周期状态
- AC-1: 评审通过，自动触发设计阶段
- AC-2: 多需求并行执行，各自状态独立隔离互不影响
- AC-3: 流程状态持久化存储，系统中断后恢复
- AC-4: 非法状态迁移请求，拒绝迁移并记录

**实现对齐**:
- `StateMachine` 类: transition, get_status, can_transition, save_state, load_state
- `StateTransitionTable` 类: is_valid, get_next
- `PersistenceManager` 类: save_state, load_state
- `Status` 枚举 (14 状态), `Event` 枚举 (10+6 事件)

---

## C. Quality Gates

| Metric | Actual | Threshold | Status |
|--------|--------|-----------|--------|
| Line Coverage | 98% | ≥ 80% | PASS |
| Branch Coverage | 98% | ≥ 70% | PASS |
| Mutation Score | N/A (Windows) | ≥ 75% | SKIPPED |

**Note**: mutmut requires WSL on Windows — mutation testing was skipped.

---

## D. Real Test Execution Summary (真实测试内容)

| Case ID | Category | Test Type | Result | Key Assertion |
|---------|----------|-----------|--------|---------------|
| ST-FUNC-007-001 | FUNC/happy | Real | PASS | REVIEW_APPROVED → IN_DESIGN auto-transition |
| ST-FUNC-007-002 | FUNC/happy | Real | PASS | DESIGN_CONFIRMED → IN_IMPLEMENTATION auto-transition |
| ST-FUNC-007-003 | FUNC/happy | Real | PASS | PENDING_REVIEW → REVIEW_APPROVED on REVIEW_PASS |
| ST-FUNC-007-004 | FUNC/happy | Real | PASS | PENDING_REVIEW → PENDING_ARBITRATION on REVIEW_REJECT |
| ST-FUNC-007-005 | FUNC/happy | Real | PASS | PENDING_ARBITRATION → REVIEW_APPROVED on ARBITRATION_APPROVE |
| ST-FUNC-007-006 | FUNC/happy | Real | PASS | PENDING_ARBITRATION → REJECTED on ARBITRATION_REJECT |
| ST-FUNC-007-007 | FUNC/happy | Real | PASS | IN_DESIGN → DESIGN_PENDING_CONFIRM on DESIGN_COMPLETE |
| ST-FUNC-007-008 | FUNC/error | Real | PASS | Invalid transition raises InvalidTransitionError |
| ST-FUNC-007-009 | FUNC/error | Real | PASS | Requirement not found raises RequirementNotFoundError |
| ST-FUNC-007-010 | FUNC/happy | Real | PASS | State persisted to database correctly |
| ST-FUNC-007-011 | FUNC/happy | Real | PASS | State loaded from database correctly |
| ST-FUNC-007-012 | FUNC/happy | Real | PASS | Multiple requirements have independent states |
| ST-BNDRY-007-001 | BNDRY/edge | Real | PASS | Empty req_id raises RequirementNotFoundError |
| ST-BNDRY-007-002 | BNDRY/edge | Real | PASS | DESIGN_RETRY with max retries → TERMINATED |
| ST-BNDRY-007-003 | BNDRY/edge | Real | PASS | IMPL_RETRY with max retries → TERMINATED |
| ST-BNDRY-007-004 | BNDRY/edge | Real | PASS | Timeout event on PENDING_ARBITRATION stays in same state |
| ST-BNDRY-007-005 | BNDRY/edge | Real | PASS | Invalid event on valid state raises InvalidTransitionError |
| ST-PERF-007-001 | PERF/load | Real | PASS | Concurrent transitions maintain data integrity |

**Total**: 18/18 PASS (100%)

---

## E. Risk Assessment with Mitigations (风险与解决办法)

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| mutmut not available on Windows | Minor | Use WSL or CI/CD for mutation testing | Accepted |
| SQLite datetime adapter deprecation | Low | Python 3.12+ deprecation warning; non-blocking | Accepted |

---

## F. Inline Compliance Check

| Check | Result | Details |
|-------|--------|---------|
| P2: Interface Contract | PASS | 3/3 interfaces verified (StateMachine, StateTransitionTable, PersistenceManager) |
| T2: Test Inventory | PASS | 18/18 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 18 |
| FUNC Cases | 12 |
| BNDRY Cases | 5 |
| UI Cases | 0 |
| SEC Cases | 0 |
| PERF Cases | 1 |
| Execution Pass Rate | 18/18 (100%) |
| Manual Cases | 0 |
| Visual Assessment | N/A (ui:false) |

---

## H. Files Changed

- `app/core/state_machine.py` (new) — StateMachine, StateTransitionTable, PersistenceManager, Status/Event enums
- `tests/test_state_machine.py` (new) — 23 test cases

---

## I. Dependencies

| Feature ID | Title | Status |
|------------|-------|--------|
| F001 | 项目骨架与基础设施 | passing |
| F002 | 数据模型与迁移 | passing |
| F003 | IM Webhook 接入 | passing |
| F004 | 需求结构化与 ID 生成 | passing |
| F005 | 状态变更指令系统 | passing |
| F006 | 查询指令系统 | passing |

---

_Report generated: 2026-07-06_
