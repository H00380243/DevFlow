# Test Case Document: 评审团多角色打分 (Feature #8)

**Feature ID**: 8
**Related Requirements**: FR-005
**Date**: 2026-07-07
**Standard**: ISO/IEC/IEEE 29119-3

## Summary

| Category | Count |
|----------|-------|
| FUNC | 10 |
| BNDRY | 4 |
| SEC | 0 |
| PERF | 1 |
| UI | 0 |
| **Total** | **15** |

## Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 15 |
| Passed | 0 |
| Failed | 0 |
| Pending | 15 |

## Manual Test Case Summary

No manual test cases — all cases are automated.

## Specification Resolutions

Specification resolutions applied from Feature Design Clarification Addendum:
- Design §2.2 defines `ReviewTeam.review()` returning `ReviewResult` (scoring + aggregation + final_verdict + state transitions). Per feature-list decomposition, F008 implements only `run_scoring() -> list[DimensionScores]`. Aggregation, final_verdict, and state transitions belong to F009.

---

## Test Cases

### ST-FUNC-008-001: 3 Agent 全部执行成功

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-001 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 |
| **Feature Design Row** | Test A |

**Preconditions**: Requirement with id="REQ-20260707-001" exists in DB with status PENDING_REVIEW.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Inject a real SQLite DB with the requirement seeded | DB ready |
| 2 | Create `ReviewTeam(session)` and mock all 3 agents' `call_llm` to return valid JSON with all scores=4, verdict="通过" | Mock configured |
| 3 | Call `team.run_scoring("REQ-20260707-001")` | Returns `list[DimensionScores]` of length 3 |
| 4 | Verify each DimensionScores has all 4 dimension scores = 4, verdict = APPROVE | All assertions pass |

**Verification Points**: 3 roles each output 4-dimension scores in 1-5 range with valid verdict.

---

### ST-FUNC-008-002: ReviewAgent.score 解析有效 JSON

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-002 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 |
| **Feature Design Row** | Test B |

**Preconditions**: StructuredRequirement with valid requirement data.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")` and mock `call_llm` to return valid JSON `{"business_value":5,"technical_feasibility":4,"roi":3,"system_compatibility":5,"verdict":"通过","comments":"good"}` | Mock configured |
| 2 | Call `agent.score(requirement)` | Returns `DimensionScores` |
| 3 | Verify agent_role="产品分析", scores as expected, verdict=APPROVE, comments="good" | All assertions pass |

**Verification Points**: Single agent correctly parses valid JSON LLM response into DimensionScores.

---

### ST-FUNC-008-003: 失败重试后成功（指数退避）

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-003 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-2 |
| **Feature Design Row** | Test C |

**Preconditions**: Requirement exists with id="REQ-20260707-001" in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewTeam(session)`, set agent's `call_llm` to fail first 2 times (ConnectionError), succeed on 3rd | Mock configured |
| 2 | Call `team._execute_agent(agent, requirement)` | Returns valid DimensionScores (not None) |
| 3 | Verify `call_llm` was called exactly 3 times | call_count == 3 |
| 4 | Verify `_notify_agent_failure` was NOT called | No failure notification sent |

**Verification Points**: Agent retries after failure, succeeds on 3rd attempt, no admin notification.

---

### ST-FUNC-008-004: 单 Agent 3 次重试耗尽后返回 None

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-004 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-2 |
| **Feature Design Row** | Test D |

**Preconditions**: Requirement exists with id="REQ-20260707-001" in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewTeam(session)`, set agent's `call_llm` to always raise ConnectionError | Mock configured |
| 2 | Call `team._execute_agent(agent, requirement)` | Returns `None` |
| 3 | Verify `call_llm` was called exactly 3 times | call_count == 3 |
| 4 | Verify `_notify_agent_failure` was called once with the agent role name | Admin notification sent |

**Verification Points**: After 3 retries exhausted, agent returns None and admin is notified.

---

### ST-FUNC-008-005: 3 Agent 全部失败 → AllAgentsFailedError

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-005 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-3 |
| **Feature Design Row** | Test E |

**Preconditions**: Requirement exists with id="REQ-20260707-001" in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewTeam(session)`, set all 3 agents' `call_llm` to always raise ConnectionError | Mock configured |
| 2 | Call `team.run_scoring("REQ-20260707-001")` | Raises `AllAgentsFailedError("REQ-20260707-001")` |
| 3 | Verify `_notify_agent_failure` was called 3 times (once per agent) | All 3 agents notified |

**Verification Points**: All 3 agents fail → scoring raises AllAgentsFailedError.

---

### ST-FUNC-008-006: 非 JSON 响应 → ScoreParseError

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-006 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 |
| **Feature Design Row** | Test F |

**Preconditions**: StructuredRequirement with valid requirement data.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")`, mock `call_llm` to return non-JSON string `"I think the score is..."` | Mock configured |
| 2 | Call `agent.score(requirement)` | Raises `ScoreParseError` |
| 3 | Verify exception contains agent role name and raw response string | Error details preserved |

**Verification Points**: Non-JSON LLM response correctly raises ScoreParseError.

---

### ST-FUNC-008-007: 评分结果持久化到 ReviewResults 表

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-007 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 |
| **Feature Design Row** | Test L |

**Preconditions**: Requirement exists with id="REQ-20260707-001" in PENDING_REVIEW status. Real SQLite DB.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewTeam(session)`, mock all 3 agents' `call_llm` to return valid JSON | Mock configured |
| 2 | Call `team.run_scoring("REQ-20260707-001")` | Returns 3 DimensionScores |
| 3 | Query `ReviewResults` table for requirement_id="REQ-20260707-001" | 3 rows found |
| 4 | Verify each row has correct agent_role, dimension scores, and verdict | All rows match mock data |

**Verification Points**: Per-agent scores correctly persisted to ReviewResults table.

---

### ST-FUNC-008-008: Prompt 构建包含角色名和需求信息

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-008 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 |
| **Feature Design Row** | Test M |

**Preconditions**: StructuredRequirement with id="REQ-20260707-001" and summary="批量导入功能".

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")`, mock `call_llm` to return valid JSON | Mock configured |
| 2 | Call `agent.score(requirement)` | Returns DimensionScores |
| 3 | Inspect the prompt passed to `call_llm` | Contains "产品分析", "REQ-20260707-001", and "批量导入功能" |

**Verification Points**: Prompt correctly includes role name and requirement details.

---

### ST-FUNC-008-009: F008 不修改需求状态

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-009 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 (boundary) |
| **Feature Design Row** | Test N |

**Preconditions**: Requirement exists with id="REQ-20260707-001" in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Verify initial status via `StateMachine.get_status("REQ-20260707-001")` | Status.PENDING_REVIEW |
| 2 | Create `ReviewTeam(session)`, mock all 3 agents' `call_llm` to return valid JSON | Mock configured |
| 3 | Call `team.run_scoring("REQ-20260707-001")` | Scoring succeeds |
| 4 | Verify final status via `StateMachine.get_status("REQ-20260707-001")` | Still Status.PENDING_REVIEW |

**Verification Points**: F008 run_scoring does NOT modify requirement status (state transitions belong to F009).

---

### ST-FUNC-008-010: 不存在需求 → RequirementNotFoundError

| Field | Value |
|-------|-------|
| **Case ID** | ST-FUNC-008-010 |
| **Category** | FUNC |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 |
| **Feature Design Row** | Test O |

**Preconditions**: No requirement with id="REQ-NONEXIST-001" exists in DB.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewTeam(session)` | Team ready |
| 2 | Call `team.run_scoring("REQ-NONEXIST-001")` | Raises `RequirementNotFoundError("REQ-NONEXIST-001")` |

**Verification Points**: Non-existent req_id correctly raises RequirementNotFoundError.

---

### ST-BNDRY-008-001: 评分边界值最小值 (1)

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-008-001 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 (boundary) |
| **Feature Design Row** | Test G |

**Preconditions**: StructuredRequirement with valid requirement data.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")`, mock `call_llm` to return `{"business_value":1,"technical_feasibility":1,"roi":1,"system_compatibility":1,"verdict":"反对"}` | Mock configured |
| 2 | Call `agent.score(requirement)` | Returns DimensionScores with all scores=1, verdict=REJECT |

**Verification Points**: Minimum boundary value (1) is accepted as valid score.

---

### ST-BNDRY-008-002: 评分边界值最大值 (5)

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-008-002 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 (boundary) |
| **Feature Design Row** | Test H |

**Preconditions**: StructuredRequirement with valid requirement data.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")`, mock `call_llm` to return `{"business_value":5,"technical_feasibility":5,"roi":5,"system_compatibility":5,"verdict":"通过"}` | Mock configured |
| 2 | Call `agent.score(requirement)` | Returns DimensionScores with all scores=5, verdict=APPROVE |

**Verification Points**: Maximum boundary value (5) is accepted as valid score.

---

### ST-BNDRY-008-003: 结论 = "中立"

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-008-003 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 (boundary) |
| **Feature Design Row** | Test I |

**Preconditions**: StructuredRequirement with valid requirement data.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")`, mock `call_llm` to return `{"business_value":3,"technical_feasibility":3,"roi":3,"system_compatibility":3,"verdict":"中立"}` | Mock configured |
| 2 | Call `agent.score(requirement)` | Returns DimensionScores with verdict=NEUTRAL |

**Verification Points**: "中立" verdict is correctly parsed and mapped to NEUTRAL enum.

---

### ST-BNDRY-008-004: 评分=0 超出范围 → ScoreParseError

| Field | Value |
|-------|-------|
| **Case ID** | ST-BNDRY-008-004 |
| **Category** | BNDRY |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-1 (boundary) |
| **Feature Design Row** | Test J |

**Preconditions**: StructuredRequirement with valid requirement data.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewAgent(role_name="产品分析")`, mock `call_llm` to return `{"business_value":0,"technical_feasibility":2,"roi":3,"system_compatibility":4,"verdict":"通过"}` | Mock configured |
| 2 | Call `agent.score(requirement)` | Raises `ScoreParseError("产品分析", ...)` |

**Verification Points**: Score=0 (out of 1-5 range) correctly raises ScoreParseError.

---

### ST-PERF-008-001: 指数退避时间验证 (1s, 2s)

| Field | Value |
|-------|-------|
| **Case ID** | ST-PERF-008-001 |
| **Category** | PERF |
| **Test Type** | Real |
| **已自动化** | Yes |
| **Traces To** | FR-005 AC-2 |
| **Feature Design Row** | Test K |

**Preconditions**: Requirement exists with id="REQ-20260707-001" in PENDING_REVIEW status.

**Test Steps**:

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create `ReviewTeam(session)`, set agent's `call_llm` to fail 2 times with ValueError (bad score parse), succeed on 3rd | Mock configured |
| 2 | Replace `time.sleep` with a mock that records sleep durations | Mock in place |
| 3 | Call `team._execute_agent(agent, requirement)` | Returns valid DimensionScores |
| 4 | Verify `time.sleep` was called 2 times with durations ~1.0s and ~2.0s | sleep(1) then sleep(2), tolerance ±0.5s |

**Verification Points**: Exponential backoff correctly sleeps 1s then 2s before 3rd attempt.

---

## Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-008-001 | FR-005 AC-1 | Test A | test_three_agents_all_succeed | PENDING |
| ST-FUNC-008-002 | FR-005 AC-1 | Test B | test_score_returns_dimension_scores | PENDING |
| ST-FUNC-008-003 | FR-005 AC-2 | Test C | test_retry_then_success | PENDING |
| ST-FUNC-008-004 | FR-005 AC-2 | Test D | test_all_retries_exhausted | PENDING |
| ST-FUNC-008-005 | FR-005 AC-3 | Test E | test_all_agents_fail_raises | PENDING |
| ST-FUNC-008-006 | FR-005 AC-1 | Test F | test_non_json_response_raises | PENDING |
| ST-FUNC-008-007 | FR-005 AC-1 | Test L | test_scores_persisted_to_db | PENDING |
| ST-FUNC-008-008 | FR-005 AC-1 | Test M | test_prompt_contains_role_and_requirement | PENDING |
| ST-FUNC-008-009 | FR-005 AC-1 | Test N | test_state_unchanged_after_scoring | PENDING |
| ST-FUNC-008-010 | FR-005 AC-1 | Test O | test_requirement_not_found | PENDING |
| ST-BNDRY-008-001 | FR-005 AC-1 | Test G | test_score_min_boundary | PENDING |
| ST-BNDRY-008-002 | FR-005 AC-1 | Test H | test_score_max_boundary | PENDING |
| ST-BNDRY-008-003 | FR-005 AC-1 | Test I | test_verdict_neutral | PENDING |
| ST-BNDRY-008-004 | FR-005 AC-1 | Test J | test_score_zero_raises | PENDING |
| ST-PERF-008-001 | FR-005 AC-2 | Test K | test_exponential_backoff_timing | PENDING |
