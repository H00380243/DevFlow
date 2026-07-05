## Goal
- Build DemandFlow (智能需求交付系统) — complete all 23 features across 7 milestones, currently on Worker cycle for F004 (需求结构化与 ID 生成).

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

### In Progress
- **F004 (需求结构化与 ID 生成): FAILING** — Orient step pending
  - Dependencies: F003 ✓
  - SRS Trace: FR-002, FR-003
  - Next: Start Orient → Bootstrap → Config Gate

### Blocked
- None

## Key Decisions
- **Approach B (Monolith + Async Workers)**: FastAPI main + Huey workers
- **SQLite WAL** for both DB and Huey queue; `data/demandflow.db` + `data/huey_queue.db`
- **F002 models**: CHECK constraints at DB level (id GLOB, ratings 1-5, verdict IN, timeout_count≥0); JSON fields (tags, skeleton_dirs, core_interfaces, risk_warnings, code_files, verification_result)
- **F003 implementation**: MessageRouter with CommandType enum (REQUIREMENT/COMMAND/UNSUPPORTED); async webhook returns 202; Huey processes message in background

## Next Steps
1. Start F004 Orient → Bootstrap → Config Gate
2. F004 Feature Detailed Design via SubAgent
3. F004 TDD Red-Green-Refactor cycle
4. F004 Quality Gates, ST, Inline Check, Persist
5. Continue F005–F023

## Critical Context
- Progress: 3/23 features passing; Next: F004
- Critical path: F001→F002→F003→F004→F007→F008→F009→F010→F011
- 23 features total, 7 milestones
- F004 key classes: `RequirementParser`, `generate_requirement_id()`, `validate_idempotency()`
- F004 contract C-002: `POST /api/requirements` accepts StructuredRequirement, returns `{requirement_id, status}`
- F004 SRS FR-002: requirement ID format `REQ-YYYYMMDD-NNN`, zero-padded sequence
- F004 SRS FR-003: 5-minute idempotency window, same sender+content → return existing ID
- Git HEAD: `977a257` (docs: update feature-list.json and task-progress.md)

## Relevant Files
- `docs/plans/2026-07-04-demandflow-srs.md` — Approved SRS (21 FRs, 11 NFRs); FR-002, FR-003 are F004's srs_trace
- `docs/plans/2026-07-04-demandflow-design.md` — Approved Design; §2.2 (需求结构化与 ID 生成), §4.2 (API contracts C-002)
- `docs/plans/2026-07-04-demandflow-ats.md` — Approved ATS
- `feature-list.json` — Task inventory (F001 passing, F002 passing, F003 passing, F004 failing)
- `task-progress.md` — Progress log (3/23, last: F003, next: F004)
- `app/__init__.py`, `app/main.py` — FastAPI app factory
- `app/core/config.py` — pydantic-settings config (DATABASE_URL, HUEY_URL, IM_PLATFORM, IM_WEBHOOK_SECRET, etc.)
- `app/core/database.py` — SQLAlchemy session (`get_db`)
- `app/core/queue.py` — Huey SQLite queue (`init_huey`)
- `app/core/webhook.py` — WebhookHandler (F003)
- `app/core/message_router.py` — MessageRouter (F003)
- `app/models.py` — 8 SQLAlchemy models + init_db + Pydantic models
- `alembic/` — Alembic migration config + `versions/0001_initial.py`
- `tests/test_app.py`, `tests/test_config.py`, `tests/test_database.py`, `tests/test_queue.py` — F001 tests
- `tests/test_models.py`, `tests/test_migration.py` — F002 tests
- `tests/test_webhook_handler.py`, `tests/test_message_router.py` — F003 tests
- `docs/features/2026-07-05-F001-project-skeleton.md` — F001 feature design
- `docs/features/2026-07-05-F002-data-model.md` — F002 feature design
- `docs/features/2026-07-05-F003-im-webhook.md` — F003 feature design
- `docs/test-cases/feature-1-project-skeleton.md` — F001 ST cases
- `docs/test-cases/feature-2-data-model.md` — F002 ST cases
- `docs/test-cases/feature-3-im-webhook.md` — F003 ST cases
- `docs/report/feature-1-project-skeleton-report.md` — F001 report
- `docs/report/feature-2-data-model-report.md` — F002 report
- `docs/report/feature-3-im-webhook-report.md` — F003 report
- `RELEASE_NOTES.md` — Updated with F001 + F002 + F003
- `long-task-guide.md` — Worker session guide
- `env-guide.md` — Service lifecycle
- `.env.example` — Environment variable template
