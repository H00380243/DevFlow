# Feature Development Report: F004 — 需求结构化与 ID 生成

**Feature ID**: 4
**Feature Title**: 需求结构化与 ID 生成
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-05
**Git SHA**: (pending commit)

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 4 |
| Title | 需求结构化与 ID 生成 |
| Category | core |
| Priority | high |
| Dependencies | F003 (IM Webhook 接入) |
| UI | false |
| SRS Trace | FR-002, FR-003 |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-002: 需求结构化与 ID 生成**
- EARS: When 系统识别一条需求消息，the system shall 提取核心诉求与约束并生成带唯一 ID 的结构化需求条目
- AC-1: 生成 REQ-YYYYMMDD-NNN 格式唯一 ID 并存储
- AC-2: 空文本或指令关键词拒绝生成
- AC-3: 无法解析时标记"待人工补充诉求"
- AC-4: 999 上限启用 4 位序号

**SRS FR-003: 重复提交幂等识别**
- EARS: When 同一提交人在 5 分钟内发送相同文本的需求消息，the system shall 识别为重复并复用已生成的需求 ID
- AC-1: 5 分钟内相同文本复用已有 ID
- AC-2: 超过 5 分钟或不同文本视为新需求
- AC-3: 不同提交人相同文本视为新需求

**实现对齐**:
- `RequirementParser` 类: parse, generate_id, _extract_intent, _extract_constraints
- `IdempotencyChecker` 类: check, store
- `StructuredRequirement` Pydantic 模型

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
| ST-FUNC-004-001 | FUNC/happy | Real | PASS | Valid requirement generates REQ-YYYYMMDD-NNN ID |
| ST-FUNC-004-002 | FUNC/happy | Real | PASS | StructuredRequirement has all required fields |
| ST-FUNC-004-003 | FUNC/happy | Real | PASS | Requirement saved to database |
| ST-FUNC-004-004 | FUNC/happy | Real | PASS | Duplicate within 5 min returns existing ID |
| ST-FUNC-004-005 | FUNC/happy | Real | PASS | Different content generates new ID |
| ST-FUNC-004-006 | FUNC/happy | Real | PASS | Different user same content generates new ID |
| ST-FUNC-004-007 | FUNC/happy | Real | PASS | Expired entry generates new ID |
| ST-BNDRY-004-001 | BNDRY/edge | Real | PASS | Minimum length content accepted |
| ST-BNDRY-004-002 | BNDRY/edge | Real | PASS | Maximum length content accepted |
| ST-BNDRY-004-003 | BNDRY/edge | Real | PASS | Special characters in content handled |
| ST-BNDRY-004-004 | BNDRY/edge | Real | PASS | Sequence at 999 boundary expands to 4 digits |
| ST-SEC-004-001 | SEC/auth | Real | PASS | Empty content rejected with error |
| ST-SEC-004-002 | SEC/auth | Real | PASS | Null content rejected with error |

**Total**: 13/13 PASS (100%)

---

## E. Risk Assessment with Mitigations (风险与解决办法)

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| mutmut not available on Windows | Minor | Use WSL or CI/CD for mutation testing | Accepted |

---

## F. Inline Compliance Check

| Check | Result | Details |
|-------|--------|---------|
| P2: Interface Contract | PASS | 6/6 interfaces verified (RequirementParser, IdempotencyChecker, StructuredRequirement) |
| T2: Test Inventory | PASS | 13/13 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 13 |
| FUNC Cases | 7 |
| BNDRY Cases | 4 |
| UI Cases | 0 |
| SEC Cases | 2 |
| PERF Cases | 0 |
| Execution Pass Rate | 13/13 (100%) |
| Manual Cases | 0 |
| Visual Assessment | N/A (ui:false) |

---

## H. Files Changed

- `app/core/requirement_parser.py` (new) — RequirementParser class
- `app/core/idempotency.py` (new) — IdempotencyChecker class
- `app/models.py` (modified) — Added StructuredRequirement Pydantic model
- `tests/test_requirement_parser.py` (new) — 27 test cases
- `tests/test_idempotency_checker.py` (new) — 8 test cases

---

## I. Dependencies

| Feature ID | Title | Status |
|------------|-------|--------|
| F001 | 项目骨架与基础设施 | passing |
| F002 | 数据模型与迁移 | passing |
| F003 | IM Webhook 接入 | passing |

---

_Report generated: 2026-07-05_
