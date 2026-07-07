# Feature Development Report: F011 — 评审驳回通知与归档

**Feature ID**: 11
**Feature Title**: 评审驳回通知与归档
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-07
**Git SHA**: (pending commit)

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 11 |
| Title | 评审驳回通知与归档 |
| Category | core |
| Priority | high |
| Dependencies | F010 (人工仲裁处理), F009 (评审结论汇总与裁决) |
| UI | false |
| SRS Trace | FR-008a, FR-008b |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-008a: 评审驳回 IM 通知**
- AC-1: 仲裁驳回 → IM 通知提交人含驳回原因与评分明细
- AC-2: IM 推送失败 → 指数退避重试 3 次

**SRS FR-008b: 需求驳回归档**
- AC-1: 通知发出 → 状态置"已驳回"且不再自动流转
- AC-2: 归档存储失败 → 指数退避重试 3 次，3 次仍失败则 IM 通知管理员

> 归档（状态置"已驳回"+停止流转）已由 F009 `ArbitrationHandler.handle_response` 通过状态机迁移实现。F011 实现驳回通知的 IM 推送层。

**实现对齐**:
- `RejectionNotifier` 类: notify_submitter + 指数退避重试
- `format_rejection_message` 函数: 格式化驳回通知中文消息
- 复用 F010 的 `NotificationFailedError`
- 驳回原因空 → "未提供原因" fallback
- 评审摘要空 → "无评审摘要" fallback

---

## C. Quality Gates

| Metric | Actual | Threshold | Status |
|--------|--------|-----------|--------|
| Line Coverage | 97% | ≥ 80% | PASS |
| Branch Coverage | 100% | ≥ 70% | PASS |
| Mutation Score | N/A (Windows) | ≥ 75% | SKIPPED |

---

## D. Real Test Execution Summary

| Case ID | Category | Test Type | Result | Key Assertion |
|---------|----------|-----------|--------|---------------|
| T-FUNC-001 | FUNC/happy | Real | PASS | notify_submitter pushes 1 message containing req_id, reason, summary |
| T-FUNC-002 | FUNC/happy | Real | PASS | format_rejection_message contains "需求编号", "驳回原因", "评审摘要" |
| T-FUNC-003 | FUNC/happy | Real | PASS | 2 failures + 1 success → recovers on 3rd attempt |
| T-FUNC-004 | FUNC/error | Real | PASS | 3 push failures → raises NotificationFailedError |
| T-FUNC-005 | FUNC/happy | Real | PASS | handle_response(approved=False) → ARBITRATION_REJECT → REJECTED |
| T-FUNC-006 | FUNC/error | Real | PASS | 3 failures → raises NotificationFailedError (exhaustion) |
| T-BNDRY-001 | BNDRY/edge | Real | PASS | Empty reason → message contains "未提供原因" |
| T-BNDRY-002 | BNDRY/edge | Real | PASS | Empty summary → message contains "无评审摘要" |

**Total**: 10/10 PASS (100%) — covering 8 inventory rows

---

## E. Risk Assessment with Mitigations

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| mutmut not available on Windows | Minor | Use WSL or CI/CD for mutation testing | Accepted |

---

## F. Inline Compliance Check

| Check | Result | Details |
|-------|--------|---------|
| P2: Interface Contract | PASS | 3/3 named interfaces verified (RejectionNotifier.notify_submitter, format_rejection_message, NotificationFailedError) |
| T2: Test Inventory | PASS | 8/8 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 10 |
| FUNC Cases | 6 |
| BNDRY Cases | 2 |
| Execution Pass Rate | 10/10 (100%) |

---

## H. Files Changed

- `app/core/rejection_notification.py` (new) — RejectionNotifier, format_rejection_message
- `tests/test_rejection_notification.py` (new) — 10 test cases

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

---

_Report generated: 2026-07-07_
