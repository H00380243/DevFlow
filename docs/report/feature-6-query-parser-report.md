# Feature Development Report: F006 — 查询指令系统

**Feature ID**: 6
**Feature Title**: 查询指令系统
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-05
**Git SHA**: (pending commit)

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 6 |
| Title | 查询指令系统 |
| Category | core |
| Priority | high |
| Dependencies | F004 (需求结构化与 ID 生成) |
| UI | false |
| SRS Trace | FR-004b |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-004b: 查询类指令解析执行**
- EARS: When 用户发送查询类指令（进度/我的列表），the system shall 解析指令并返回对应结果
- AC-1: 提交人发送"进度 REQ-xxx"，返回该需求当前阶段与状态
- AC-2: 提交人发送"我的列表"，返回该提交人所有需求的列表
- AC-3: 进度查询的需求 ID 不存在，返回错误提示"需求 REQ-xxx 不存在"
- AC-4: 指令格式错误或缺少必要参数，返回正确指令格式提示

**实现对齐**:
- `CommandParser` 类: parse, _parse_progress, _parse_list
- `QueryExecutor` 类: execute_query, _execute_progress, _execute_list
- `ProgressCommand`, `ListCommand` 数据类

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
| ST-FUNC-006-001 | FUNC/happy | Real | PASS | Valid progress command parsed correctly |
| ST-FUNC-006-002 | FUNC/happy | Real | PASS | Valid list command parsed correctly |
| ST-FUNC-006-003 | FUNC/happy | Real | PASS | Progress executor returns stage/status |
| ST-FUNC-006-004 | FUNC/happy | Real | PASS | List executor returns formatted list |
| ST-FUNC-006-005 | FUNC/error | Real | PASS | Progress not found returns error |
| ST-FUNC-006-006 | FUNC/error | Real | PASS | Missing REQ ID returns format error |
| ST-FUNC-006-007 | FUNC/error | Real | PASS | Unrecognized prefix returns format error |
| ST-BNDRY-006-001 | BNDRY/edge | Real | PASS | None input raises CommandParseError |
| ST-BNDRY-006-002 | BNDRY/edge | Real | PASS | Empty string raises CommandParseError |
| ST-BNDRY-006-003 | BNDRY/edge | Real | PASS | Whitespace-only input raises CommandParseError |
| ST-BNDRY-006-004 | BNDRY/edge | Real | PASS | Double space after 进度 parsed correctly |
| ST-BNDRY-006-005 | BNDRY/edge | Real | PASS | Leading/trailing spaces stripped |
| ST-BNDRY-006-006 | BNDRY/edge | Real | PASS | Extra text after 我的列表 rejected |
| ST-BNDRY-006-007 | BNDRY/edge | Real | PASS | Empty list returns ok with friendly message |
| ST-BNDRY-006-008 | BNDRY/edge | Real | PASS | Invalid REQ ID format rejected |

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
| P2: Interface Contract | PASS | 2/2 interfaces verified (CommandParser, QueryExecutor) |
| T2: Test Inventory | PASS | 15/15 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 15 |
| FUNC Cases | 7 |
| BNDRY Cases | 8 |
| UI Cases | 0 |
| SEC Cases | 0 |
| PERF Cases | 0 |
| Execution Pass Rate | 15/15 (100%) |
| Manual Cases | 0 |
| Visual Assessment | N/A (ui:false) |

---

## H. Files Changed

- `app/core/command_parser.py` (modified) — Added ProgressCommand, ListCommand, _parse_progress, _parse_list
- `app/core/command_executor.py` (modified) — Added QueryExecutor class
- `tests/test_query_parser.py` (new) — 15 test cases

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
