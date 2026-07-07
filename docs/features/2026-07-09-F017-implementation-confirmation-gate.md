# Feature Detailed Design: 实施确认门 (Feature #17)

**Date**: 2026-07-09
**Feature**: #17 — 实施确认门
**Priority**: high
**Dependencies**: [16] (F016 冲烟验证 — provides VerificationResult)
**Design Reference**: docs/plans/2026-07-04-demandflow-design.md § 2.4
**SRS Reference**: FR-015

## Context

实现实施确认门，对 F015+F016 输出的实施结果进行 IM 推送、确认/驳回处理、4 小时超时监控、3 轮迭代上限。与 F014 设计确认门结构一致。

## Design Alignment

§2.4.4 实施确认门：
- **提交人确认**: 状态流转 IMPL_PENDING_ACCEPTANCE → IMPL_APPROVED → DELIVERED（自动）
- **提交人驳回**: 状态流转 IMPL_PENDING_ACCEPTANCE → IMPL_REJECTED → IN_IMPLEMENTATION / TERMINATED
- **超时提醒**: 4 小时无操作 → IM 提醒；3 次后升级管理员

## State Machine Impact

需要新增一条迁移：
- `(Status.IMPL_PENDING_ACCEPTANCE, Event.TIMEOUT): Status.IMPL_PENDING_ACCEPTANCE` — 超时自循环

## Interface Contract

| Method | Signature | Preconditions | Postconditions | Raises |
|--------|-----------|---------------|----------------|--------|
| `start_confirmation_gate` | `(req_id, verification_result, submitter_id) -> None` | req_id exists, status=IMPL_PENDING_ACCEPTANCE | IM push with verification summary | NotificationFailedError (after 3 retries) |
| `handle_confirm` | `(req_id, sender_id) -> None` | req_id exists | Transition IMPL_CONFIRM → IMPL_APPROVED → DELIVERED, IM confirm | RequirementNotFoundError, InvalidTransitionError |
| `handle_reject` | `(req_id, sender_id, reason) -> None` | req_id exists, reason non-empty | Transition IMPL_REJECT, retry/terminate, IM notify | EmptyRejectReasonError |

## Test Inventory

| ID | Category | Traces To | Input / Setup | Expected |
|----|----------|-----------|---------------|----------|
| T001 | FUNC/happy | FR-015 AC-1 | start_confirmation_gate(valid req) | IM push sent, no error |
| T002 | FUNC/happy | FR-015 AC-2 | handle_confirm(valid req) | Transition to IMPL_APPROVED → DELIVERED |
| T003 | FUNC/happy | FR-015 AC-3 | handle_reject(valid req, "需修改") | Transition IMPL_REJECTED → IN_IMPLEMENTATION, IM notify |
| T004 | FUNC/error | FR-015 AC-4 | Max retry (3rd reject) | Transition TERMINATED, IM notify admin |
| T005 | BNDRY/edge | — | start_confirmation_gate(wrong state) | No-op (return) |
| T006 | BNDRY/edge | — | handle_confirm(nonexistent req) | RequirementNotFoundError |
| T007 | BNDRY/edge | FR-015 AC-5 | Timeout reminder after 4h | IM reminder, TIMEOUT self-loop |
| T008 | BNDRY/edge | FR-015 AC-5 | Timeout escalation after 3rd | Admin escalation |
| T009 | BNDRY/edge | — | handle_reject(empty reason) | EmptyRejectReasonError |
| T010 | BNDRY/edge | — | handle_reject(none reason) | EmptyRejectReasonError |
| T011 | BNDRY/edge | — | Non-submitter confirm/reject | Permission denied |
| T012 | BNDRY/edge | — | Push retry 3x then fail | NotificationFailedError |
| T013 | BNDRY/edge | — | Push recover on 2nd retry | Success |
| T014 | BNDRY/edge | — | Timeout count boundary (2→3) | Reminder 2→escalation 3 |
| T015 | FUNC/happy | — | Retry: first reject redesign | IN_IMPLEMENTATION state |
| T016 | BNDRY/edge | — | handle_confirm after already confirmed | InvalidTransitionError |
| T017 | BNDRY/edge | — | Timeout with DB failure | Graceful return [] |

Negative ratio: 13/17 = 76.5% ≥ 40% ✅
