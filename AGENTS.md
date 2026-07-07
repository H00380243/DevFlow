## Goal
- Build DemandFlow (智能需求交付系统) — complete all 23 features across 7 milestones, currently on Worker cycle for F011 (评审驳回通知与归档).

## Constraints & Preferences
- SQLite replaces PostgreSQL; Huey with SQLite backend (both DB and queue)
- IM platform: single channel, configurable (dingtalk/feishu/slack)
- Tech stack: FastAPI, SQLAlchemy, LangChain/LangGraph, React + Ant Design 5.x + AntV G6
- Language: All user-facing output in Chinese (Simplified)
- Quality gates: line ≥80%, branch ≥70%, mutation ≥75%
- mutmut requires WSL on Windows — mutation testing skipped, manual mutation as project methodology

## Progress
### Done
- All planning phases complete (SRS, UCD, Design, ATS, Init)
- **F001 (项目骨架与基础设施): PASS** — git `e0c4404`
  - FastAPI app factory (`create_app`), SQLite+WAL DB (`get_db`), Huey queue (`init_huey`), pydantic-settings config (`get_settings`)
  - 12 tests, 96% line / 98% branch coverage, 11/11 ST cases PASS
  - Report: `docs/report/feature-1-project-skeleton-report.md`
- **F002 (数据模型与迁移): PASS** — git `f59520f`
  - 8 SQLAlchemy models (Requirements, ReviewResults, DesignResults, ImplementationResults, DeliveryArchives, StatusHistory, ArbitrationRequests, IdempotencyStore)
  - CHECK constraints, JSON fields, composite index, Alembic initial migration
  - 41 total tests (29 F002-specific), 98% line / 98% branch coverage, 28/28 ST cases PASS
  - Report: `docs/report/feature-2-data-model-report.md`
- **F003 (IM Webhook 接入): PASS** — git `f7c9a7c`
  - WebhookHandler, MessageRouter, POST /webhook/im/{platform} endpoint
  - 63 total tests (22 F003-specific), 96% line / 96% branch coverage, 12/12 ST cases PASS
  - Report: `docs/report/feature-3-im-webhook-report.md`
- **F004 (需求结构化与 ID 生成): PASS** — git `d1565b3`
  - RequirementParser, IdempotencyChecker, StructuredRequirement Pydantic model
  - 98 total tests (35 F004-specific), 97% line / 97% branch coverage, 13/13 ST cases PASS
  - Report: `docs/report/feature-4-requirement-parser-report.md`
- **F005 (状态变更指令系统): PASS** — git `ee85144`
  - CommandParser, PermissionChecker, CommandExecutor
  - 129 total tests (31 F005-specific), 97% line / 97% branch coverage, 15/15 ST cases PASS
  - Report: `docs/report/feature-5-command-parser-report.md`
- **F006 (查询指令系统): PASS** — git `b1303b4`
  - CommandParser extensions (ProgressCommand, ListCommand), QueryExecutor
  - 144 total tests (15 F006-specific), 97% line / 97% branch coverage, 15/15 ST cases PASS
  - Report: `docs/report/feature-6-query-parser-report.md`
- **F007 (状态机引擎): PASS** — git `8779ae5`
  - StateMachine, StateTransitionTable, PersistenceManager, Status/Event enums
  - 167 total tests (23 F007-specific), 98% line / 98% branch coverage, 18/18 ST cases PASS
  - Report: `docs/report/feature-7-state-machine-report.md`
- **F008 (评审团多角色打分): PASS** — git `ddd60da`
  - ReviewTeam, ReviewAgent, DimensionScores, Verdict, retry_with_backoff
  - 182 total tests (15 F008-specific), 96% line / ~93% branch coverage, ST skipped (user requested)
  - Report: `docs/report/feature-8-review-scoring-report.md`
- **F009 (评审结论汇总与裁决): PASS** — git `c5921d4`
  - AggregationService, ArbitrationHandler, FinalDecision, _decide pure function
  - 裁决规则: ≥2 APPROVE → auto-pass, ≥2 REJECT → arbitration, else → auto-pass
  - 200 total tests (18 F009-specific), 98% line / 98% branch coverage, ST skipped (user requested)
  - Report: `docs/report/feature-9-review-aggregation-report.md`
- **F010 (人工仲裁处理): PASS** — git `0a78664`
  - ArbitrationNotifier, ArbitrationTimeoutMonitor, CommandExecutor arbitration routing
  - IM push retry 3x 指数退避, 4-hour timeout escalation, state-aware command routing
  - 214 total tests (14 F010-specific), 98% line / 100% branch (arbitration_notification), ST skipped
  - Report: `docs/report/feature-10-arbitration-notification-report.md`

### In Progress
- **F011 (评审驳回通知与归档): FAILING** — Orient step pending
  - Dependencies: F010 ✓
  - SRS Trace: FR-008a, FR-008b
  - Next: Start Orient → Bootstrap → Config Gate

### Blocked
- None

### Blocked
- None

## Key Decisions
- **Approach B (Monolith + Async Workers)**: FastAPI main + Huey workers
- **SQLite WAL** for both DB and Huey queue; `data/demandflow.db` + `data/huey_queue.db`
- **F002 models**: CHECK constraints at DB level (id GLOB, ratings 1-5, verdict IN, timeout_count≥0); JSON fields (tags, skeleton_dirs, core_interfaces, risk_warnings, code_files, verification_result)
- **F003 implementation**: MessageRouter with CommandType enum (REQUIREMENT/COMMAND/UNSUPPORTED); async webhook returns 202; Huey processes message in background
- **F004 implementation**: RequirementParser with generate_id() using REQ-YYYYMMDD-NNN format; IdempotencyChecker with 5-minute window
- **F005 implementation**: CommandParser with confirm/reject parsing; PermissionChecker with submitter-only validation; CommandExecutor orchestrating parse → permission → DB ops
- **F006 implementation**: CommandParser extended with _parse_progress/_parse_list; QueryExecutor handling progress/list queries; no permission check for query commands
- **F007 implementation**: StateMachine with StateTransitionTable and PersistenceManager; 14 Status states, 10+6 Events, 16 valid transitions
- **F008 implementation**: ReviewTeam with 3 parallel ReviewAgents (产品分析/价值评估/技术可行性); DimensionScores 4-dimension 1-5 scoring; Verdict enum; retry_with_backoff exponential backoff
- **F009 implementation**: AggregationService with _decide pure function; ArbitrationHandler managing arbitration lifecycle (request, response, timeout, escalation); FinalDecision enum (APPROVED/NEEDS_ARBITRATION)
- **F010 implementation**: ArbitrationNotifier with IM push retry 3x backoff; ArbitrationTimeoutMonitor with 4-hour timeout and 3-step escalation; CommandExecutor extended with state-aware arbitration routing

## Next Steps
1. F011 Orient → Bootstrap → Config Gate
2. F011 Feature Detailed Design via SubAgent
3. F011 TDD Red-Green-Refactor cycle
4. Continue F012–F023

## Critical Context
- Progress: 10/23 features passing; Next: F011
- Critical path: F001→F002→F003→F004→F007→F008→F009→F010→F011
- 23 features total, 7 milestones
- F010 key classes: ArbitrationNotifier, ArbitrationTimeoutMonitor, NotificationFailedError, TimeoutResult
- F010 SRS FR-007: IM推送仲裁请求给管理员、超时4小时提醒、3次升级
- F010 depends on F009 (ArbitrationHandler) and F007 (StateMachine)
- Git HEAD: `0a78664` (feat(F010): 人工仲裁处理)

## Relevant Files
- `docs/plans/2026-07-04-demandflow-srs.md` — Approved SRS (21 FRs, 11 NFRs); FR-004b is F006's srs_trace
- `docs/plans/2026-07-04-demandflow-design.md` — Approved Design; §2.1 (IM integration), §4.2 (API contracts)
- `docs/plans/2026-07-04-demandflow-ats.md` — Approved ATS
- `feature-list.json` — Task inventory (F001-F010 passing, F011 failing)
- `task-progress.md` — Progress log (10/23, last: F010, next: F011)
- `app/__init__.py`, `app/main.py` — FastAPI app factory
- `app/core/config.py` — pydantic-settings config (DATABASE_URL, HUEY_URL, IM_PLATFORM, IM_WEBHOOK_SECRET, etc.)
- `app/core/database.py` — SQLAlchemy session (`get_db`)
- `app/core/queue.py` — Huey SQLite queue (`init_huey`)
- `app/core/webhook.py` — WebhookHandler (F003)
- `app/core/message_router.py` — MessageRouter (F003)
- `app/core/requirement_parser.py` — RequirementParser (F004)
- `app/core/idempotency.py` — IdempotencyChecker (F004)
- `app/core/command_parser.py` — CommandParser (F005)
- `app/core/permission_checker.py` — PermissionChecker (F005)
- `app/core/command_executor.py` — CommandExecutor (F005)
- `app/core/state_machine.py` — StateMachine (F007)
- `app/core/review_scoring.py` — ReviewTeam, ReviewAgent (F008)
- `app/core/review_aggregation.py` — AggregationService, ArbitrationHandler (F009)
- `app/core/arbitration_notification.py` — ArbitrationNotifier, ArbitrationTimeoutMonitor (F010)
- `app/models.py` — 8 SQLAlchemy models + init_db + Pydantic models
- `alembic/` — Alembic migration config + `versions/0001_initial.py`
- `tests/test_app.py`, `tests/test_config.py`, `tests/test_database.py`, `tests/test_queue.py` — F001 tests
- `tests/test_models.py`, `tests/test_migration.py` — F002 tests
- `tests/test_webhook_handler.py`, `tests/test_message_router.py` — F003 tests
- `tests/test_requirement_parser.py`, `tests/test_idempotency_checker.py` — F004 tests
- `tests/test_command_parser.py`, `tests/test_permission_checker.py`, `tests/test_command_executor.py` — F005 tests
- `tests/test_query_parser.py` — F006 tests
- `tests/test_state_machine.py` — F007 tests
- `tests/test_review_scoring.py` — F008 tests
- `tests/test_review_aggregation.py` — F009 tests
- `tests/test_arbitration_notification.py` — F010 tests
- `docs/features/2026-07-05-F001-project-skeleton.md` — F001 feature design
- `docs/features/2026-07-05-F002-data-model.md` — F002 feature design
- `docs/features/2026-07-05-F003-im-webhook.md` — F003 feature design
- `docs/features/2026-07-05-F004-requirement-parser.md` — F004 feature design
- `docs/features/2026-07-05-F005-command-parser.md` — F005 feature design
- `docs/features/2026-07-05-F006-query-parser.md` — F006 feature design
- `docs/features/2026-07-05-F007-state-machine.md` — F007 feature design
- `docs/features/2026-07-07-F008-review-scoring.md` — F008 feature design
- `docs/features/2026-07-07-F009-review-aggregation.md` — F009 feature design
- `docs/features/2026-07-07-F010-arbitration-notification.md` — F010 feature design
- `docs/test-cases/feature-1-project-skeleton.md` — F001 ST cases
- `docs/test-cases/feature-2-data-model.md` — F002 ST cases
- `docs/test-cases/feature-3-im-webhook.md` — F003 ST cases
- `docs/test-cases/feature-4-requirement-parser.md` — F004 ST cases
- `docs/test-cases/feature-5-command-parser.md` — F005 ST cases
- `docs/test-cases/feature-6-query-parser.md` — F006 ST cases
- `docs/test-cases/feature-7-state-machine.md` — F007 ST cases
- `docs/test-cases/feature-8-review-scoring.md` — F008 ST cases
- `docs/test-cases/feature-9-review-aggregation.md` — F009 ST cases (generated from design)
- `docs/report/feature-1-project-skeleton-report.md` — F001 report
- `docs/report/feature-2-data-model-report.md` — F002 report
- `docs/report/feature-3-im-webhook-report.md` — F003 report
- `docs/report/feature-4-requirement-parser-report.md` — F004 report
- `docs/report/feature-5-command-parser-report.md` — F005 report
- `docs/report/feature-6-query-parser-report.md` — F006 report
- `docs/report/feature-7-state-machine-report.md` — F007 report
- `docs/report/feature-8-review-scoring-report.md` — F008 report
- `docs/report/feature-9-review-aggregation-report.md` — F009 report
- `docs/report/feature-10-arbitration-notification-report.md` — F010 report
- `RELEASE_NOTES.md` — Updated with F001+F002+F003+F004+F005+F006+F007+F008+F009+F010
- `long-task-guide.md` — Worker session guide
- `env-guide.md` — Service lifecycle
- `.env.example` — Environment variable template
