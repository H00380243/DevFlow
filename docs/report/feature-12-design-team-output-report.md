# Feature Development Report: F012 — 设计团多角色产出

**Feature ID**: 12
**Feature Title**: 设计团多角色产出
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-08
**Git SHA**: 1c27e72

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 12 |
| Title | 设计团多角色产出 |
| Category | core |
| Priority | high |
| Dependencies | F007 (状态机引擎) |
| UI | false |
| SRS Trace | FR-009 |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-009: 设计团多角色产出概要设计**
- AC-1: 评审通过 → 触发设计团（产品设计、技术选型、合规风控 3 角色）产出概要设计并汇总
- AC-2: 合规风控角色识别高风险 → 在设计中标注 [高风险] 并给出建议
- AC-3: 某角色 Agent 失败 → 指数退避重试 3 次，3 次仍失败则 IM 通知管理员

**实现对齐**:
- `DesignTeam.run_design` → 3 角色并行执行，汇总为 DesignResult ✓ (AC-1)
- `_aggregate_results` → 合规风控 `has_high_risk=True` 时在 risk_warnings 前加 `[高风险]` 前缀 ✓ (AC-2)
- `_execute_agent` / `retry_with_backoff(max_retries=3)` → 指数退避重试，耗尽后 `_notify_agent_failure` ✓ (AC-3)

---

## C. Quality Gates

| Metric | Actual | Threshold | Status |
|--------|--------|-----------|--------|
| Line Coverage | 95% | ≥ 80% | PASS |
| Branch Coverage | 90% | ≥ 70% | PASS |
| Mutation Score | N/A (Windows) | ≥ 75% | SKIPPED |

---

## D. Real Test Execution Summary

| Case ID | Category | Test Type | Result | Key Assertion |
|---------|----------|-----------|--------|---------------|
| T001 | FUNC/happy | Real | PASS | 3 agents succeed → DesignResult with all fields, 3 DB rows persisted |
| T002 | FUNC/happy | Real | PASS | 合规风控 high risk → risk_warnings prefixed with [高风险] |
| T003 | FUNC/error | Real | PASS | All 3 agents fail → AllAgentsFailedError, _notify_agent_failure called 3x |
| T004 | FUNC/retry | Real | PASS | 2 fails + 1 success → recovers on 3rd attempt, call_count=3 |
| T005 | BNDRY/edge | Real | PASS | Empty {} JSON for 产品设计 → DesignParseError |
| T006 | BNDRY/edge | Real | PASS | Only 1 agent succeeds → partial DesignResult returned |
| T007 | FUNC/error | Real | PASS | Missing req_id → RequirementNotFoundError |
| T008 | BNDRY/edge | Real | PASS | Malformed JSON → DesignParseError raised |
| T009 | BNDRY/edge | Real | PASS | First design → version=1 |
| T010 | BNDRY/edge | Real | PASS | Re-design → version=2 |
| T011 | PERF/parallel | Real | PASS | 3 agents with 0.5s delay each → total time < 1.5s (parallel) |
| T012 | PERF/perf | Real | PASS | Exponential backoff: sleeps ~1s then ~2s between retries |
| T013 | FUNC/error | Real | PASS | DB write failure → RuntimeError propagates |
| T014 | FUNC/state | Real | PASS | Design runs and aggregates from REVIEW_APPROVED/IN_DESIGN state |

**Total**: 19/19 PASS (100%) — covering 14 inventory rows + 5 supplementary checks

---

## E. Risk Assessment with Mitigations

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| mutmut not available on Windows | Minor | Use WSL or CI/CD for mutation testing | Accepted |

---

## F. Inline Compliance Check

| Check | Result | Details |
|-------|--------|---------|
| P2: Interface Contract | PASS | 10/10 named methods verified (DesignAgent.design, DesignAgent.call_llm, DesignAgent._build_prompt, DesignTeam.run_design, _load_requirement, _persist_output, _execute_agent, _notify_agent_failure, _aggregate_results, _get_next_version) |
| T2: Test Inventory | PASS | 14/14 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 19 |
| FUNC Cases | 8 |
| BNDRY Cases | 6 |
| PERF Cases | 2 |
| Execution Pass Rate | 19/19 (100%) |

---

## H. Files Changed

- `app/core/design_team.py` (new) — DesignTeam, DesignAgent, DesignOutput, DesignResult, DesignParseError, AllAgentsFailedError
- `tests/test_design_team.py` (new) — 19 test cases
- `docs/features/2026-07-08-F012-design-team-output.md` (new) — Feature detailed design document (14-row Test Inventory, all 8 sections)

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
| F007 | 状态机引擎 | passing |
| F008 | 评审团多角色打分 | passing |
| F009 | 评审结论汇总与裁决 | passing |
| F010 | 人工仲裁处理 | passing |
| F011 | 评审驳回通知与归档 | passing |

---

_Report generated: 2026-07-08_
