## Goal
- Build DemandFlow (智能需求交付系统) — complete all 23 features across 7 milestones, currently on Worker cycle for F006 (查询指令系统).

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

### In Progress
- **F006 (查询指令系统): FAILING** — Orient step pending
  - Dependencies: F004 ✓
  - SRS Trace: FR-004b
  - Next: Start Orient → Bootstrap → Config Gate

### Blocked
- None

## Key Decisions
- **Approach B (Monolith + Async Workers)**: FastAPI main + Huey workers
- **SQLite WAL** for both DB and Huey queue; `data/demandflow.db` + `data/huey_queue.db`
- **F002 models**: CHECK constraints at DB level (id GLOB, ratings 1-5, verdict IN, timeout_count≥0); JSON fields (tags, skeleton_dirs, core_interfaces, risk_warnings, code_files, verification_result)
- **F003 implementation**: MessageRouter with CommandType enum (REQUIREMENT/COMMAND/UNSUPPORTED); async webhook returns 202; Huey processes message in background
- **F004 implementation**: RequirementParser with generate_id() using REQ-YYYYMMDD-NNN format; IdempotencyChecker with 5-minute window
- **F005 implementation**: CommandParser with confirm/reject parsing; PermissionChecker with submitter-only validation; CommandExecutor orchestrating parse → permission → DB ops

## Next Steps
1. Start F006 Orient → Bootstrap → Config Gate
2. F006 Feature Detailed Design via SubAgent
3. F006 TDD Red-Green-Refactor cycle
4. F006 Quality Gates, ST, Inline Check, Persist
5. Continue F007–F023

## Critical Context
- Progress: 5/23 features passing; Next: F006
- Critical path: F001→F002→F003→F004→F007→F008→F009→F010→F011
- 23 features total, 7 milestones
- F006 key classes: `QueryParser`, `ProgressQuery`, `ListQuery`
- F006 contract C-004: `POST /api/queries` accepts Query, returns `{status, data}`
- F006 SRS FR-004b: progress/list queries with permission validation
- Git HEAD: `b95bbff` (docs: update feature-list.json and task-progress.md)

## Relevant Files
- `docs/plans/2026-07-04-demandflow-srs.md` — Approved SRS (21 FRs, 11 NFRs); FR-004b is F006's srs_trace
- `docs/plans/2026-07-04-demandflow-design.md` — Approved Design; §2.1 (IM integration), §4.2 (API contracts C-004)
- `docs/plans/2026-07-04-demandflow-ats.md` — Approved ATS
- `feature-list.json` — Task inventory (F001-F005 passing, F006 failing)
- `task-progress.md` — Progress log (5/23, last: F005, next: F006)
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
- `app/models.py` — 8 SQLAlchemy models + init_db + Pydantic models
- `alembic/` — Alembic migration config + `versions/0001_initial.py`
- `tests/test_app.py`, `tests/test_config.py`, `tests/test_database.py`, `tests/test_queue.py` — F001 tests
- `tests/test_models.py`, `tests/test_migration.py` — F002 tests
- `tests/test_webhook_handler.py`, `tests/test_message_router.py` — F003 tests
- `tests/test_requirement_parser.py`, `tests/test_idempotency_checker.py` — F004 tests
- `tests/test_command_parser.py`, `tests/test_permission_checker.py`, `tests/test_command_executor.py` — F005 tests
- `docs/features/2026-07-05-F001-project-skeleton.md` — F001 feature design
- `docs/features/2026-07-05-F002-data-model.md` — F002 feature design
- `docs/features/2026-07-05-F003-im-webhook.md` — F003 feature design
- `docs/features/2026-07-05-F004-requirement-parser.md` — F004 feature design
- `docs/features/2026-07-05-F005-command-parser.md` — F005 feature design
- `docs/test-cases/feature-1-project-skeleton.md` — F001 ST cases
- `docs/test-cases/feature-2-data-model.md` — F002 ST cases
- `docs/test-cases/feature-3-im-webhook.md` — F003 ST cases
- `docs/test-cases/feature-4-requirement-parser.md` — F004 ST cases
- `docs/test-cases/feature-5-command-parser.md` — F005 ST cases
- `docs/report/feature-1-project-skeleton-report.md` — F001 report
- `docs/report/feature-2-data-model-report.md` — F002 report
- `docs/report/feature-3-im-webhook-report.md` — F003 report
- `docs/report/feature-4-requirement-parser-report.md` — F004 report
- `docs/report/feature-5-command-parser-report.md` — F005 report
- `RELEASE_NOTES.md` — Updated with F001 + F002 + F003 + F004 + F005
- `long-task-guide.md` — Worker session guide
- `env-guide.md` — Service lifecycle
- `.env.example` — Environment variable template
