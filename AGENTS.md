## Goal
- Build DemandFlow (智能需求交付系统) — currently on M8 (Code Agent 适配层), all 23 original features passing (ST GO verdict).

## Constraints & Preferences
- SQLite replaces PostgreSQL; Huey with SQLite backend (both DB and queue)
- IM platform: single channel, configurable (dingtalk/feishu/slack)
- Tech stack: FastAPI, SQLAlchemy, React + Ant Design 5.x + AntV G6
- Language: All user-facing output in Chinese (Simplified)
- Code Agent stack: Claude Code CLI (primary), pluggable adapter registry
- Quality gates: line ≥80%, branch ≥70%, mutation ≥75%
- mutmut requires WSL on Windows — mutation testing skipped, manual mutation as project methodology

## Progress
### v1 Done (F001–F023)
All 23 features passing across 7 milestones. ST concluded with GO verdict: 26/26 tests pass, 463 total tests, 0 defects, 100% RTM.
- **F001 (项目骨架与基础设施): PASS** — git `e0c4404`
- **F002 (数据模型与迁移): PASS** — git `f59520f`
- **F003 (IM Webhook 接入): PASS** — git `f7c9a7c`
- **F004 (需求结构化与 ID 生成): PASS** — git `d1565b3`
- **F005 (状态变更指令系统): PASS** — git `ee85144`
- **F006 (查询指令系统): PASS** — git `b1303b4`
- **F007 (状态机引擎): PASS** — git `8779ae5`
- **F008 (评审团多角色打分): PASS** — git `ddd60da`
- **F009 (评审结论汇总与裁决): PASS** — git `c5921d4`
- **F010 (人工仲裁处理): PASS** — git `0a78664`
- **F011 (评审驳回通知与归档): PASS** — git `5e1a0ca`
- **F012 (设计团多角色产出): PASS** — git `1c27e72`
- **F013 (设计产出物生成): PASS** — git `c92dce9`
- **F014 (设计确认门与迭代): PASS** — git `718f373`
- **F015 (实施团代码生成): PASS** — git `8ca5496`
- **F016 (冲烟验证): PASS** — git `1680713`
- **F017 (实施确认门): PASS** — git `e25036e`
- **F018 (Git 提交与密钥检测): PASS** — git `fee99aa`
- **F019 (交付档案与状态归档): PASS** — git `ed166c2`
- **F020 (看板首页指标): PASS** — git `b9f6b5c`
- **F021 (需求列表与筛选搜索): PASS** — git `b6aaf9a`
- **F022 (需求详情页): PASS** — git `5b5e800`
- **F023 (看板操作与 IM 同步): PASS** — git `176c65c`
- ST Report: `docs/plans/2026-07-09-st-report.md`

### v2 In Progress (M8–M13)
- **F024 (CodeAgentAdapter 抽象与 Registry): PASS** — pending commit
  - `app/core/adapters/__init__.py`, `app/core/adapters/base.py`
  - Capability/TaskSpec/OutputContract/Workspace/AgentRunResult/CodeAgentAdapter(ABC)/CodeAgentRegistry
  - 12 tests, all pass
- **F025 (WorkspaceManager worktree 隔离): PASS** — pending commit
  - `app/core/workspace_manager.py`
  - acquire/release/cleanup with git worktree isolation
  - 4 tests, all pass
- **F026 (ClaudeCodeAdapter): PASS** — pending commit
  - `app/core/adapters/claude_adapter.py`
  - CLI subprocess execution, JSON output parsing, artifact scanning
  - 10 tests, all pass
- **F027 (评审团委托适配器): PASS** — pending commit
  - Refactored `ReviewAgent.score()` to support `adapter.execute()` via `_score_via_adapter`
  - `CodeAgentEngine` integration helper (`app/core/adapters/engine.py`)
  - Backward compatible: `call_llm` still works when no adapter provided
  - 15 new tests (F027-specific), 74 total in adapter layer, all pass
- **F028 (设计团委托适配器): PASS** — pending commit
  - Refactored `DesignAgent.design()` to support `adapter.execute()` via `_design_via_adapter`
  - `DesignTeam` accepts optional `adapter` + `workspace_manager`
  - Backward compatible: `call_llm` still works when no adapter provided
  - 11 new tests (F028-specific), 85 total in adapter layer, all pass
- **F029 (实施团委托适配器): PASS** — pending commit
  - Refactored `ImplementationAgent.generate()` to support `adapter.execute()` via `_build_task_spec` + `_parse_result`
  - `ImplementationTeam` accepts optional `adapter` + `workspace_manager`
  - Backward compatible: `call_llm` still works when no adapter provided
  - 10 new tests (F029-specific), 95 total in adapter layer, all pass
- **F030 (TestRunner 完整测试验收): PASS** — pending commit
  - `TestResult` pydantic model with `passed_with_gate()` gate check (line ≥80%, branch ≥70%)
  - `TestRunner` class with capability-based degradation (`Capability.RUN_TESTS`)
  - `_build_task_spec` / `_parse_result` / `run_tests(workspace)` adapter delegation pattern
  - Integrated into `ImplementationTeam.run_implementation()` — runs tests after code gen, persists `test_result` + `worktree_path` to `ImplementationResults`
  - Added `worktree_path`, `test_result`, `coverage` columns to `ImplementationResults` model
  - Backward compatible: no TestRunner → no tests run, original flow unchanged
  - 25 new tests, 156 total in adapter layer + implementation team, all pass

## Next Steps
- Commit F024–F030 and push
- Proceed to F031 (Git 落盘接通 worktree)

## Key Decisions
- **v2 CON-003 rewrite**: execution layer from LangChain+stub LLM → pluggable Code Agent CLI via unified adapter contract
- **adapter layer** (`app/core/adapters/`): CodeAgentAdapter ABC + Registry; ClaudeCodeAdapter as default; `capabilities()` for provider capability discovery
- **worktree isolation** (`WorkspaceManager`): each requirement+stage gets a dedicated git worktree for isolated execution
- **LangChain/minio removed**: all v1 LangChain dependencies stripped from requirements

## Relevant Files
### v1 Core
- `app/__init__.py`, `app/main.py` — FastAPI app factory
- `app/core/config.py` — pydantic-settings config (all env vars including v2: CODE_AGENT_PROVIDER, CLI_PATH, TIMEOUT_SEC, WORKTREE_BASE_DIR/RETENTION_DAYS, GIT_REPO_DIR, LLM_BASE_URL, LLM_MODEL_NAME)
- `app/core/database.py` — SQLAlchemy session
- `app/core/queue.py` — Huey SQLite queue
- `app/core/state_machine.py` — StateMachine (F007)
- `app/models.py` — 8 SQLAlchemy models
- `alembic/` — Alembic migration config
- `start.cmd` — double-click dev launcher
- `scripts/seed_demo.py` — 6 seed requirements

### v2 Adapter Layer
- `app/core/adapters/__init__.py` — module exports
- `app/core/adapters/base.py` — F024: Capability, TaskSpec, OutputContract, Workspace, AgentRunResult, CodeAgentAdapter, CodeAgentRegistry
- `app/core/adapters/claude_adapter.py` — F026: ClaudeCodeAdapter
- `app/core/workspace_manager.py` — F025: WorkspaceManager

### Docs
- `docs/plans/2026-07-08-demandflow-srs.md` — SRS v2 (CON-003 rewrite, FR-022/023/024)
- `docs/plans/2026-07-08-demandflow-design.md` — Design v2 (§2.7 adapter contract, M8–M13)
- `docs/plans/2026-07-09-st-report.md` — ST report
- `feature-list.json` — F024–F035 defined
