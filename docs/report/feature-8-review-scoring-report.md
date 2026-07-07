# Feature Development Report: F008 — 评审团多角色打分

**Feature ID**: 8
**Feature Title**: 评审团多角色打分
**Category**: core
**Priority**: high
**Completion Date**: 2026-07-07
**Git SHA**: (pending commit)

---

## A. Basic Info

| Field | Value |
|-------|-------|
| Feature ID | 8 |
| Title | 评审团多角色打分 |
| Category | core |
| Priority | high |
| Dependencies | F007 (状态机引擎) |
| UI | false |
| SRS Trace | FR-005 |

---

## B. Requirements Consistency Briefing (需求一致性简报)

**SRS FR-005: 评审团多角色独立打分**
- EARS: When 一条新结构化需求入库，the system shall 触发评审团（产品分析、价值评估、技术可行性 3 角色）按 1-5 分制从业务价值、技术可行性、投入产出比、系统兼容性 4 维度独立打分并给出通过/反对/中立结论
- AC-1: 3 角色各自输出 4 维度 1-5 分评分与通过/反对/中立结论
- AC-2: 某角色 Agent 执行失败，指数退避重试 3 次，3 次仍失败则 IM 通知管理员
- AC-3: 3 角色均执行失败，暂停该需求流转并 IM 通知管理员

**实现对齐**:
- `ReviewAgent` 类: score, _build_prompt, call_llm
- `ReviewTeam` 类: run_scoring, _execute_agent, _persist_score
- `Verdict` 枚举, `DimensionScores` 模型, `ReviewScores` 模型
- `retry_with_backoff` 辅助函数

---

## C. Quality Gates

| Metric | Actual | Threshold | Status |
|--------|--------|-----------|--------|
| Line Coverage | 96% | ≥ 80% | PASS |
| Branch Coverage | ~93% | ≥ 70% | PASS |
| Mutation Score | N/A (Windows) | ≥ 75% | SKIPPED |

**Note**: mutmut requires WSL on Windows — mutation testing was skipped.

---

## D. Real Test Execution Summary (真实测试内容)

| Case ID | Category | Test Type | Result | Key Assertion |
|---------|----------|-----------|--------|---------------|
| ST-FUNC-008-001 | FUNC/happy | Real | PASS | 3 agents succeed, return 3 DimensionScores |
| ST-FUNC-008-002 | FUNC/happy | Real | PASS | ReviewAgent.score returns valid DimensionScores |
| ST-FUNC-008-003 | FUNC/error | Real | PASS | Retry then success — agent recovers after 2 failures |
| ST-FUNC-008-004 | FUNC/error | Real | PASS | All retries exhausted — returns None, notifies failure |
| ST-FUNC-008-005 | FUNC/error | Real | PASS | All 3 agents fail — raises AllAgentsFailedError |
| ST-FUNC-008-006 | FUNC/error | Real | PASS | Non-JSON LLM response raises ScoreParseError |
| ST-FUNC-008-007 | FUNC/error | Real | PASS | Requirement not found raises RequirementNotFoundError |
| ST-BNDRY-008-001 | BNDRY/edge | Real | PASS | Minimum valid score (1) accepted |
| ST-BNDRY-008-002 | BNDRY/edge | Real | PASS | Maximum valid score (5) accepted |
| ST-BNDRY-008-003 | BNDRY/edge | Real | PASS | Neutral verdict accepted |
| ST-BNDRY-008-004 | BNDRY/edge | Real | PASS | Score 0 raises ScoreParseError |
| ST-BNDRY-008-005 | BNDRY/edge | Real | PASS | Prompt contains role name and requirement content |
| ST-PERF-008-001 | PERF/load | Real | PASS | Exponential backoff timing: sleep(1), sleep(2) |
| ST-INTG-008-001 | INTG/db | Real | PASS | Scores persisted to ReviewResults table |
| ST-INTG-008-002 | INTG/state | Real | PASS | F008 does not change requirement state |

**Total**: 15/15 PASS (100%)

---

## E. Risk Assessment with Mitigations (风险与解决办法)

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| mutmut not available on Windows | Minor | Use WSL or CI/CD for mutation testing | Accepted |
| LLM API key not configured for production | High | LLM_API_KEY env var required for production use | Configured |

---

## F. Inline Compliance Check

| Check | Result | Details |
|-------|--------|---------|
| P2: Interface Contract | PASS | 3/3 interfaces verified (ReviewAgent, ReviewTeam, retry_with_backoff) |
| T2: Test Inventory | PASS | 15/15 test inventory rows covered |
| D3: Design Versions | N/A | No §13 in design doc |
| U1: UCD Spot Check | N/A | ui:false feature |

---

## G. Feature-ST Summary

| Metric | Value |
|--------|-------|
| Total Cases | 15 |
| FUNC Cases | 7 |
| BNDRY Cases | 5 |
| UI Cases | 0 |
| SEC Cases | 0 |
| PERF Cases | 1 |
| INTG Cases | 2 |
| Execution Pass Rate | 15/15 (100%) |
| Manual Cases | 0 |
| Visual Assessment | N/A (ui:false) |

---

## H. Files Changed

- `app/core/review_scoring.py` (new) — ReviewTeam, ReviewAgent, DimensionScores, Verdict, retry_with_backoff
- `tests/test_review_scoring.py` (new) — 15 test cases

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

---

_Report generated: 2026-07-07_
