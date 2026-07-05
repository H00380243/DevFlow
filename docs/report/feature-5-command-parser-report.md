# Feature Development Report: F005 — 状态变更指令系统

**Feature ID**: 5
**Feature Title**: 状态变更指令系统
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-05
**Git SHA**: (pending commit)

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 5 |
| Title | 状态变更指令系统 |
| Category | core |
| Priority | high |
| Dependencies | F004 (需求结构化与 ID 生成) |
| UI | false |
| SRS Trace | FR-004a |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-004a: 状态变更类指令解析执行**
- EARS: When 用户发送状态变更类指令（确认/驳回），the system shall 校验提交人权限后解析指令并执行对应操作
- AC-1: 提交人发送"确认 REQ-xxx"，触发对应节点确认流转
- AC-2: 提交人发送"驳回 REQ-xxx 修改意见XXX"，携带意见回退到对应阶段
- AC-3: 非提交人发送"确认/驳回 REQ-xxx"，拒绝并 IM 提示"无权限：仅提交人可操作"
- AC-4: 指令格式错误或需求 ID 不存在，IM 提示正确指令格式

**实现对齐**:
- `CommandParser` 类: parse, _parse_confirm, _parse_reject
- `PermissionChecker` 类: check_permission
- `CommandExecutor` 类: execute
- `Command`, `ConfirmCommand`, `RejectCommand` 数据类

---

## C. Quality Gates

| Metric | Actual | Threshold | Status |
|--------|--------|-----------|--------|
| Line Coverage | 97% | ≥ 80% | PASS |
| Branch Coverage | 97% | ≥ 70% | PASS |
| Mutation Score | N/A (Windows) | ≥ 75% | SKIPPED |

**Note**: mutmut requires WSL on Windows — mutation testing was skipped.

---

## D. Real Test Execution Summary (真实测试内容)

| Case ID | Category | Test Type | Result | Key Assertion |
|---------|----------|-----------|--------|---------------|
| ST-FUNC-005-001 | FUNC/happy | Real | PASS | Valid confirm command parsed correctly |
| ST-FUNC-005-002 | FUNC/happy | Real | PASS | Valid reject command with reason parsed |
| ST-FUNC-005-003 | FUNC/happy | Real | PASS | Command executed successfully |
| ST-FUNC-005-004 | FUNC/happy | Real | PASS | Status history recorded |
| ST-FUNC-005-005 | FUNC/happy | Real | PASS | Permission granted for submitter |
| ST-FUNC-005-006 | FUNC/happy | Real | PASS | Permission denied for non-submitter |
| ST-FUNC-005-007 | FUNC/happy | Real | PASS | Requirement not found returns error |
| ST-BNDRY-005-001 | BNDRY/edge | Real | PASS | Empty command text rejected |
| ST-BNDRY-005-002 | BNDRY/edge | Real | PASS | Maximum length command accepted |
| ST-BNDRY-005-003 | BNDRY/edge | Real | PASS | Special characters in reason handled |
| ST-BNDRY-005-004 | BNDRY/edge | Real | PASS | Command with extra spaces parsed |
| ST-BNDRY-005-005 | BNDRY/edge | Real | PASS | Case-insensitive command keywords |
| ST-BNDRY-005-006 | BNDRY/edge | Real | PASS | Unicode characters in reason handled |
| ST-SEC-005-001 | SEC/authz | Real | PASS | Non-submitter permission denied |
| ST-SEC-005-002 | SEC/authz | Real | PASS | Invalid requirement ID permission denied |

**Total**: 15/15 PASS (100%)

---

## E. Risk Assessment with Mitigations (风险与解决办法)

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| mutmut not available on Windows | Minor | Use WSL or CI/CD for mutation testing | Accepted |

---

## F. Inline Compliance Check

| Check | Result | Details |
|-------|--------|---------|
| P2: Interface Contract | PASS | 3/3 interfaces verified (CommandParser, PermissionChecker, CommandExecutor) |
| T2: Test Inventory | PASS | 15/15 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 15 |
| FUNC Cases | 7 |
| BNDRY Cases | 6 |
| UI Cases | 0 |
| SEC Cases | 2 |
| PERF Cases | 0 |
| Execution Pass Rate | 15/15 (100%) |
| Manual Cases | 0 |
| Visual Assessment | N/A (ui:false) |

---

## H. Files Changed

- `app/core/command_parser.py` (new) — CommandParser class
- `app/core/permission_checker.py` (new) — PermissionChecker class
- `app/core/command_executor.py` (new) — CommandExecutor class
- `tests/test_command_parser.py` (new) — 16 test cases
- `tests/test_permission_checker.py` (new) — 4 test cases
- `tests/test_command_executor.py` (new) — 11 test cases

---

## I. Dependencies

| Feature ID | Title | Status |
|------------|-------|--------|
| F001 | 项目骨架与基础设施 | passing |
| F002 | 数据模型与迁移 | passing |
| F003 | IM Webhook 接入 | passing |
| F004 | 需求结构化与 ID 生成 | passing |

---

_Report generated: 2026-07-05_
