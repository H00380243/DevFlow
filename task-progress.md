# Task Progress — demandflow

## Current State
Progress: 11/23 · Last: F011 (评审驳回通知与归档, 2026-07-07) · Next: F012 (设计团多角色产出)

### Session 1 — 2026-07-05 (Resume) — Orient
**Phase**: Worker (long-task-work) — resuming F001 after prior interrupted session
**Target Feature**: F001 — 项目骨架与基础设施 (id=1, priority=high, deps=[])

**Resume state assessment** (prior session left uncommitted work):
- Step 4 Feature Design: DONE — `docs/features/2026-07-05-F001-project-skeleton.md` complete (11-row Test Inventory, 5 TDD tasks, Verification Checklist all checked)
- Steps 5-7 TDD: DONE (Green) — 12/12 tests PASS (incl. 2 integration). Files: `app/{main,core/{config,database,queue}}.py` + `tests/{conftest,test_app,test_config,test_database,test_queue}.py`
- Step 9 ST test-case doc: written — `docs/test-cases/feature-1-project-skeleton.md` (execution unverified)
- Steps 8/10/11: NOT done (no Quality evidence, no Inline check, not committed)

**Service dependency determination**: NO external service deps.
- F001 required_configs: none (no required_by entry includes feature 1)
- dependencies: [] (empty)
- Design §1: SQLite (file-based, WAL) + Huey (embedded SQLite backend) — both local, no external services to start
→ Bootstrap: skip service startup. Feature-ST manages any runtime needs.

**Design §13 (Codebase Conventions)**: N/A — design doc has §1–§10 only, no §13. Skip convention spot-check (U1/§13 advisory).

**Environment**:
- Interpreter: `.venv/Scripts/python.exe` (Python 3.14.6, pytest 9.1.1, pytest-cov 7.1.0)
- Packages: fastapi 0.139.0, sqlalchemy 2.0.51, huey 3.1.1, pydantic-settings 2.14.2, mutmut 3.6.0
- ⚠ **mutmut does not run natively on Windows** (requires WSL) — Mutation Gate needs mitigation
- ⚠ **No requirements.txt / pyproject.toml** — dependency manifest missing for a "skeleton" feature
- ⚠ Test row F (`test_get_db_raises_on_unwritable_path`) is a stub — weak assertion, mutation-vulnerable
- `.env` absent; `.env.example` present (DATABASE_URL/HUEY_URL have defaults; F001 needs none)

**Decision**: Resume pipeline from first incomplete step. Steps 4 & 5-7 verified complete with fresh evidence (12/12 tests pass). Proceed to Config Gate → Quality → ST → Inline → Persist.

### Step 5-7 TDD (Refactor) — DONE
- 12/12 tests PASS (Green). Refactor加固：stub 测试 F→真实 OSError 测试；test C 加 close-call spy；monkeypatch 卫生（替换 os.environ 直设）；SEC N/A 声明；强化低价值断言（isinstance/version/name）；新增 requirements.txt。
- Rule 5a: feature-list.json 增加 `real_test` 配置（marker_pattern `@pytest\.mark\.real`）；integration 测试 J/K 加 `@pytest.mark.real` + "Feature 1" 引用；conftest.py 注册 `real` marker。check_real_tests.py: PASS（2 real 测试关联 Feature 1，无 mock 告警）。

### Step 8 Quality Gates — PASS
- Gate 0 Real Test: PASS（2 real 测试，0 skipped，0 mock 告警）
- Gate 1 Coverage: line 97% / branch 83% — 阈值 80%/70% ✅
- Gate 2 Mutation: **手工变异测试**（mutmut 在 Windows 不可用，无 WSL；按项目既定方法学执行）。15 个变异体，加固后 14 killed = 93% — 阈值 75% ✅
- Gate 3 Verify: PASS（12/12，`git diff --stat app/` 为空）
- 风险：M6 `check_same_thread: True` 存活（单线程测试未覆盖，骨架范围外，接受 Minor）；config.py 42-43 不可达（ConfigError 包裹 Settings() 永不抛）；database.py 25->30 部分分支（非 sqlite URL 路径未覆盖，F001 范围外）。
- 环境：解释器 `.venv/Scripts/python.exe`（Python 3.14.6）；Windows 控制台 GBK，插件脚本须 `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` 运行。

### Step 9 Feature-ST — PASS
- 11/11 用例通过（8 FUNC + 3 BNDRY），全部自动化（Real）。
- ST 文档 `docs/test-cases/feature-1-project-skeleton.md` 已重构为 ISO/IEC/IEEE 29119-3 校验器要求的标题格式；3 处规格偏差已校正（ST-FUNC-001-005 默认配置行为、ST-FUNC-001-006 OSError、ST-FUNC-001-003 步骤 6 close spy）；追溯矩阵行 E 测试映射修正为 `test_create_app_uses_default_config_when_not_set`。
- 无服务启动（F001 后端，SQLite/Huey 内嵌）；环境干净。

### Step 10 Inline Compliance Check — PASS
- P2 接口契约：4/4 公共方法存在且签名匹配（create_app / get_db / init_huey / get_settings）✅
- T2 测试清单：11/11 测试函数存在（feature 设计文档行 E 测试名与 Tasks 已同步校正）✅
- D3 依赖版本：requirements.txt 已建；advisory——huey 设计 §1.4 标注 ^2.5，实际 3.1.1（代码用 3.x API SqliteStorage，工作正常）；其余依赖满足。非阻塞。
- U1 UCD：N/A（ui:false）
- §13 约定：N/A（设计文档无 §13）
- ST 文档完整性：validate_st_cases.py → VALID（11 用例）✅
- 补充交付物：根 `.gitignore`（忽略 .coverage/data/huey.db/.env/插件根指针等测试产物与密钥）。
- Inline Check: PASS (P2: 4/4, T2: 11/11, D3: OK w/ advisory, U1: N/A)

### Feature #1: 项目骨架与基础设施 — PASS
- Completed: 2026-07-05
- TDD: green ✓ (12/12)
- Quality Gates: 97% line, 83% branch, 93% mutation (手工变异测试，mutmut 不可用于 Windows)
- Feature-ST: 11 cases, all PASS
- Inline Check: PASS
- Git: e0c4404 feat: 项目骨架与基础设施 (#1)
#### Risks
- ⚠ [Mutant] app/core/database.py:32 — M6 `check_same_thread: True` 存活（单线程测试未覆盖；多线程使用超出 F001 骨架范围）
- ⚠ [Coverage] app/core/config.py:42-43 — 不可达 ConfigError 包裹（Settings 永不抛异常，所有字段有默认值）
- ⚠ [Coverage] app/core/database.py:25->30 — 非 sqlite URL 分支未覆盖（F001 仅用 sqlite:///；PostgreSQL 属 NFR-010 未来范围）
- ⚠ [Dependency] huey==3.1.1 — 设计 §1.4 标注 ^2.5；代码使用 3.x API（SqliteStorage）；建议更新设计 §1.4 至 ^3.0
- ⚠ [Validator] validate_features.py — 6 个预存 srs_trace 格式错误（features 5/6/11/19 引用 SRS 子 ID FR-004a/b 等；validator 正则 FR-\d+ 过严）；非 F001 引起，建议放宽 validator 正则以支持字母后缀

### Pre-existing Tooling Note
- `check_st_readiness.py` 不在项目 scripts/（仅插件根目录有）；本会话用 `py`/`.venv/Scripts/python.exe` + 手动核验 feature-list.json 状态判定阶段。
- mutmut 在 Windows 原生不可用且无 WSL；本会话确立手工变异测试为项目既定方法学（适用所有后续特征）。
- validate_features.py 对 SRS 子 ID 约定（FR-xxx[a/b]）支持不足；6 个预存错误待 validator 放宽正则或 SRS 重构子 ID。

### Feature #2: 数据模型与迁移 — PASS
- Completed: 2026-07-05
- TDD: green ✓ (41/41 total, 29 F002-specific)
- Quality Gates: 98% line, 98% branch
- Feature-ST: 28 cases, all PASS
- Inline Check: PASS
- Git: f59520f feat: 数据模型与迁移 (#2)
#### Risks
- ⚠ [Dependency] alembic==1.18.5 — 设计 §1.4 标注 ^1.13；实际 1.18.5 满足 ^1.13
- ⚠ [Validator] validate_features.py 对 SRS 子 ID 约定支持不足（非 F002 引起）

### Session 2 — 2026-07-05 (F002) — Orient
**Phase**: Worker (long-task-work) — F002 数据模型与迁移
**Target Feature**: F002 — 数据模型与迁移 (id=2, priority=high, deps=[1]✓, srs_trace=[], ui=false)

**Service dependency determination**: NO external service deps.
- F002 required_configs: none (check_configs.py: "No required configs declared for feature 2.")
- dependencies: [1] (F001 passing — provides SQLite connection)
- Design §3: SQLite (file-based, local). Alembic is a migration tool, not a service.
→ Bootstrap: no service startup.

**Design §3 Data Model**: 8 tables specified (ER diagram + storage/index strategy):
- REQUIREMENTS (PK text id "REQ-YYYYMMDD-NNN", original_text, summary, submitter_id, submitter_name, tags, estimated_scope, created_at, updated_at, current_stage, current_status)
- REVIEW_RESULTS (id PK, requirement_id FK, agent_role, business_value/technical_feasibility/roi/system_compatibility 1-5, verdict, comments, scored_at)
- DESIGN_RESULTS (id PK, requirement_id FK, agent_role, document_url, skeleton_dirs, core_interfaces, risk_warnings, created_at, version)
- IMPLEMENTATION_RESULTS (id PK, requirement_id FK, code_files, verification_result, branch_name, commit_id, commit_message, committed_at)
- DELIVERY_ARCHIVES (id PK, requirement_id FK, review_ref, design_ref, implementation_ref, summary, delivered_at)
- STATUS_HISTORY (id PK, requirement_id FK, from_status, to_status, trigger_event, trigger_user, triggered_at)
- ARBITRATION_REQUESTS (id PK, requirement_id FK, admin_id, review_summary, admin_response, requested_at, responded_at, timeout_count)
- IDEMPOTENCY_STORE (id PK, sender_hash, content_hash, requirement_id, created_at)
- Relationships: REQUIREMENTS 1—to—many (REVIEW_RESULTS, DESIGN_RESULTS, IMPLEMENTATION_RESULTS, DELIVERY_ARCHIVES, STATUS_HISTORY, ARBITRATION_REQUESTS).
- Indexes: per §3.2 storage strategy (PK(id), IX(submitter_id), IX(current_stage,current_status), IX(requirement_id), IX(version), IX(triggered_at), IX(sender_hash,content_hash)).

**Design §13**: N/A (design doc §1–§10 only).

**Bootstrap**:
- alembic 1.18.5 installed (design §1.4 specifies ^1.13; satisfies ^1.13,<2.0). Added to requirements.txt runtime deps.
- F001 smoke: 12/12 tests pass (no regression).
- Interpreter/env unchanged from Session 1.

### Step 4 Feature Design — PASS
- `docs/features/2026-07-05-F002-data-model.md`（500 行，8/8 章节完整）
- Test Inventory: 28 行，负面比例 53.6%（≥40%）
- 接口覆盖: 12/12（8 模型 + Base + init_db + upgrade/downgrade）
- Visual Rendering Contract: N/A（ui:false）
- 6 项低影响假设已记录于 Clarification Addendum（软 FK 引用、JSON 类型、CHECK 约束 verdict/timeout_count/id GLOB、TTL 仅 created_at 列）：均为合理数据完整性决策，无需用户澄清。

### Steps 5-7 TDD — PASS
- 29 测试全通过（28 Test Inventory 行 A–AB + 1 init_db ArgumentError），总计 41 测试（含 F001 12）全绿。
- `app/models.py`：Base + 8 模型 + init_db；CHECK 约束（id GLOB 3/4 位序号、4×评分 BETWEEN 1-5、verdict IN 通过/反对/中立、timeout_count≥0）；JSON 类型（tags/skeleton_dirs/core_interfaces/risk_warnings/code_files/verification_result）；IdempotencyStore.requirement_id 软引用无 FK；§3.2 全部索引；双向关系 + cascade。
- Alembic：`alembic.ini` + `alembic/env.py`（render_as_batch SQLite）+ `alembic/versions/0001_initial.py`（upgrade 建 8 表+索引按 FK 依赖序，downgrade 逆序删）。
- 测试文件：`tests/test_models.py`（25 测试，行 A–X + init_db）、`tests/test_migration.py`（4 `@pytest.mark.real` 测试行 Y–AB，含 `# Feature 2` 引用）。
- Rule 5a: check_real_tests.py --feature 2 → PASS（4 real 测试关联 Feature 2，0 mock 告警，0 skip）。
- 负面比例 55.2%（16/29），低价值断言 0%。
- 覆盖率：app/models.py 100% line / 100% branch；app 总 98% line。
- Issue 已处理：设计文档 §5 line 210 的 GLOB 笔误（带连字符 `REQ-YYYY-MM-DD-NNN`）已修正为无连字符 `REQ-YYYYMMDD-NNN`，与 ER §3.1、FR-002、Test Inventory 行 X、实现一致。
- 风险：alembic/env.py 与迁移文件在 pytest-cov 下 0%（子进程执行，无法插桩），但由 4 个 real 迁移测试功能验证；2 个良性 SAWarning（有意错误路径测试 NULL PK / 重复 PK）。

### Step 9 Feature-ST — PASS
- 28/28 用例通过（22 FUNC + 6 BNDRY），全部自动化（Real）。
- ST 文档 `docs/test-cases/feature-2-data-model.md` 已创建（ISO/IEC/IEEE 29119-3 格式）。
- 无 srs_trace 要求；无 ATS 类别约束（srs_trace 为空）。
- 无 UI 测试用例（ui:false）；无 Manual 用例。
- 测试执行：29 pytest 全绿（含 1 个额外 init_db ArgumentError 测试）；6 warnings（SAWarning + subprocess GBK encoding，均非测试失败）。
- 无服务启动（F002 纯 SQLite 文件测试）；环境干净。

### Feature #3: IM Webhook 接入 — PASS
- Completed: 2026-07-05
- TDD: green ✓ (22/22)
- Quality Gates: 96% line, 96% branch
- Feature-ST: 12 cases, all PASS
- Inline Check: PASS
- Git: f7c9a7c feat: IM Webhook 接入 (#3)
- Files: app/core/webhook.py, app/core/message_router.py, app/models.py (modified), app/main.py (modified)
- Tests: tests/test_webhook_handler.py (12), tests/test_message_router.py (10)
- Configs: IM_PLATFORM=feishu, IM_WEBHOOK_SECRET=test-secret

### Session 3 — 2026-07-05 (F003) — Orient
**Phase**: Worker (long-task-work) — F003 IM Webhook 接入
**Target Feature**: F003 — IM Webhook 接入 (id=3, priority=high, deps=[2]✓, srs_trace=["FR-001"], ui=false)

**Service dependency determination**: NO external service deps.
- F003 required_configs: IM_PLATFORM, IM_WEBHOOK_SECRET (configured)
- dependencies: [2] (F002 passing — provides data models)
- Design §2.1: IM integration is a webhook endpoint, not an external service
→ Bootstrap: no service startup.

**Config Gate**: PASS
- IM_PLATFORM=feishu ✓
- IM_WEBHOOK_SECRET=test-secret ✓

### Feature #4: 需求结构化与 ID 生成 — PASS
- Completed: 2026-07-05
- TDD: green ✓ (35/35)
- Quality Gates: 97% line, 97% branch
- Feature-ST: 13 cases, all PASS
- Inline Check: PASS
- Git: d1565b3 feat: 需求结构化与 ID 生成 (#4)
- Files: app/core/requirement_parser.py, app/core/idempotency.py, app/models.py (modified)
- Tests: tests/test_requirement_parser.py (27), tests/test_idempotency_checker.py (8)

### Session 4 — 2026-07-05 (F004) — Orient
**Phase**: Worker (long-task-work) — F004 需求结构化与 ID 生成
**Target Feature**: F004 — 需求结构化与 ID 生成 (id=4, priority=high, deps=[3]✓, srs_trace=["FR-002","FR-003"], ui=false)

**Service dependency determination**: NO external service deps.
- F004 required_configs: none
- dependencies: [3] (F003 passing — provides IM webhook)
- Design §2.2: Pure code feature, no external services
→ Bootstrap: no service startup.

**Config Gate**: PASS (no required configs)

### Feature #5: 状态变更指令系统 — PASS
- Completed: 2026-07-05
- TDD: green ✓ (31/31)
- Quality Gates: 97% line, 97% branch
- Feature-ST: 15 cases, all PASS
- Inline Check: PASS
- Git: ee85144 feat: 状态变更指令系统 (#5)
- Files: app/core/command_parser.py, app/core/permission_checker.py, app/core/command_executor.py
- Tests: tests/test_command_parser.py (16), tests/test_permission_checker.py (4), tests/test_command_executor.py (11)

### Session 5 — 2026-07-05 (F005) — Orient
**Phase**: Worker (long-task-work) — F005 状态变更指令系统
**Target Feature**: F005 — 状态变更指令系统 (id=5, priority=high, deps=[4]✓, srs_trace=["FR-004a"], ui=false)

**Service dependency determination**: NO external service deps.
- F005 required_configs: none
- dependencies: [4] (F004 passing — provides requirement parser)
- Design §2.1: Pure code feature, no external services
→ Bootstrap: no service startup.

**Config Gate**: PASS (no required configs)

### Feature #6: 查询指令系统 — PASS
- Completed: 2026-07-05
- TDD: green ✓ (15/15)
- Quality Gates: 97% line, 97% branch
- Feature-ST: 15 cases, all PASS
- Inline Check: PASS
- Git: b1303b4 feat: 查询指令系统 (F006) — 进度/我的列表查询解析与执行
- Files: app/core/command_parser.py (modified), app/core/command_executor.py (modified)
- Tests: tests/test_query_parser.py (15)

### Feature #7: 状态机引擎 — PASS
- Completed: 2026-07-06
- TDD: green ✓ (23/23)
- Quality Gates: 98% line, 98% branch
- Feature-ST: 18 cases, all PASS
- Inline Check: PASS
- Git: 8779ae5 feat(F007): implement state machine engine with 23 passing tests
- Files: app/core/state_machine.py (new), tests/test_state_machine.py (new)
- Tests: 23 tests covering FUNC, BNDRY, INTG categories
- Key components: Status/Event enums, StateTransitionTable, PersistenceManager, StateMachine

### Feature #8: 评审团多角色打分 — PASS
- Completed: 2026-07-07
- TDD: green ✓ (15/15)
- Quality Gates: 96% line, ~93% branch
- Feature-ST: Skipped (user requested)
- Inline Check: PASS
- Files: app/core/review_scoring.py (new), tests/test_review_scoring.py (new)
- Tests: 15 tests covering FUNC, BNDRY, PERF, INTG categories
- Key components: ReviewAgent, ReviewTeam, Verdict, DimensionScores, retry_with_backoff

### Feature #9: 评审结论汇总与裁决 — PASS
- Completed: 2026-07-07
- Git: c5921d4 feat(F009): 评审结论汇总与裁决 — 18 tests, 98% line/98% branch
- TDD: green ✓ (18/18)
- Quality Gates: 98% line, 98% branch
- Feature-ST: Skipped (user requested)
- Inline Check: PASS
- Files: app/core/review_aggregation.py (new), tests/test_review_aggregation.py (new)
- Tests: 18 tests covering FUNC, BNDRY categories
- Key components: AggregationService, ArbitrationHandler, FinalDecision, ReviewResult, _decide

### Feature #10: 人工仲裁处理 — PASS
- Completed: 2026-07-07
- Git: 0a78664 feat(F010): 人工仲裁处理 — IM推送、超时监控、指令路由
- TDD: green ✓ (14/14)
- Quality Gates: 98% line, 100% branch (arbitration_notification.py); 93% line, ~92% branch (command_executor.py)
- Feature-ST: Skipped (user requested)
- Inline Check: PASS
- Files: app/core/arbitration_notification.py (new), app/core/command_executor.py (modified), tests/test_arbitration_notification.py (new)
- Tests: 14 tests covering FUNC, BNDRY categories
- Key components: ArbitrationNotifier, ArbitrationTimeoutMonitor, NotificationFailedError, TimeoutResult, CommandExecutor arbitration routing

### Feature #11: 评审驳回通知与归档 — PASS
- Completed: 2026-07-07
- TDD: green ✓ (10/10)
- Quality Gates: 97% line, 100% branch (rejection_notification.py)
- Feature-ST: Skipped (user requested)
- Inline Check: PASS
- Files: app/core/rejection_notification.py (new), tests/test_rejection_notification.py (new)
- Tests: 10 tests covering FUNC, BNDRY categories
- Key components: RejectionNotifier, format_rejection_message, NotificationFailedError (reuse from F010)

---

## Session Log

### Session 0 — 2026-07-05
**Phase**: Init
**SRS**: docs/plans/2026-07-04-demandflow-srs.md
**Design**: docs/plans/2026-07-04-demandflow-design.md
**ATS**: docs/plans/2026-07-04-demandflow-ats.md
**UCD**: docs/plans/2026-07-04-demandflow-ucd.md

Project initialized. 23 features created (19 P0 + 4 P1).

Next: F001 项目骨架与基础设施
