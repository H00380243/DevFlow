# Feature Acceptance Test Cases: F001 — 项目骨架与基础设施

**Feature ID**: 1
**Feature Title**: 项目骨架与基础设施
**Date**: 2026-07-05
**Standard**: ISO/IEC/IEEE 29119-3
**Related Requirements**: N/A (srs_trace empty — infrastructure feature with no direct SRS requirement)
**Design Reference**: docs/features/2026-07-05-F001-project-skeleton.md

> Specification notes: F001 is a backend-only infrastructure feature (`ui: false`)
> with an empty `srs_trace`. Per the feature design's Boundary Decisions table,
> `DATABASE_URL` and `HUEY_URL` have default values (`sqlite:///data/demandflow.db`
> and `sqlite:///data/huey_queue.db` respectively), so unsetting them does NOT raise
> an error — the implementation uses defaults. Three ST cases (005, 006, 003-step-6)
> were corrected to match real implementation behavior (see Clarification notes below).

## Summary

| Category | Count |
|----------|-------|
| FUNC     | 8     |
| BNDRY    | 3     |
| UI       | 0     |
| SEC      | 0     |
| PERF     | 0     |
| **Total**| **11**|

### Case ID
ST-FUNC-001-001

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `create_app()` returns a valid FastAPI instance with correct title and version

### Preconditions
- Project directory exists with `app/main.py` module
- Environment variables `DATABASE_URL` and `HUEY_URL` are set (or defaults exist)
- Python virtual environment activated

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Import `create_app` from `app.main` | Import succeeds without error |
| 2 | Call `create_app()` | Returns a FastAPI instance |
| 3 | Assert `app.title == "DemandFlow"` | Title matches expected string |
| 4 | Assert `app.version == "0.1.0"` | Version matches expected string |
| 5 | Assert `app` is instance of `FastAPI` | Type check passes |
| 6 | Assert `app.state.huey` is not None | Huey instance attached to app state |

### Verification Points
- FastAPI instance created with expected title and version
- Huey instance attached to application state
- No exceptions raised during creation

### Post-Conditions
- No persistent state changes; test environment restored

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_app.py::TestCreateApp::test_create_app_returns_fastapi_instance

### Case ID
ST-FUNC-001-002

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `get_settings()` loads environment variables into a Settings instance

### Preconditions
- `app/core/config.py` module exists
- Environment variables `DATABASE_URL`, `HUEY_URL` are set

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Set `DATABASE_URL=sqlite:///data/test.db` | Variable set |
| 2 | Set `HUEY_URL=sqlite:///data/test_huey.db` | Variable set |
| 3 | Import `get_settings` from `app.core.config` | Import succeeds |
| 4 | Call `get_settings()` | Returns a Settings instance |
| 5 | Assert `settings.DATABASE_URL == "sqlite:///data/test.db"` | Field matches env value |
| 6 | Assert `settings.HUEY_URL == "sqlite:///data/test_huey.db"` | Field matches env value |

### Verification Points
- Settings instance created from environment variables
- All fields populated from env values
- No ValidationError raised

### Post-Conditions
- No persistent state changes; test environment restored

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_config.py::TestGetSettings::test_get_settings_loads_env_vars

### Case ID
ST-FUNC-001-003

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `get_db()` returns an open SQLAlchemy Session and closes it when the generator exhausts

### Preconditions
- `app/core/database.py` module exists
- `DATABASE_URL` points to a writable SQLite path (temp directory)
- SQLAlchemy session lifecycle uses generator/finally pattern

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Import `get_db` from `app.core.database` | Import succeeds |
| 2 | Call `get_db()` generator | Returns generator object |
| 3 | Call `next(gen)` to obtain session | Returns SQLAlchemy Session instance |
| 4 | Assert `session.is_active` is True | Session is usable while in scope |
| 5 | Call `next(gen)` to resume past yield (triggers finally block) | StopIteration raised (generator exhausted) |
| 6 | Verify `session.close()` is invoked when the generator exhausts (verified via call-spy in the automated test) | `session.close()` called exactly once by the finally block |

### Verification Points
- Session object returned from generator
- Session is active while in scope
- `session.close()` invoked exactly once when generator exhausts (verified via call-spy; `is_active` does not reflect closed state in SQLAlchemy 2.0)

### Post-Conditions
- Session closed; no lingering connections

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_database.py::TestGetDb::test_get_db_returns_session_and_closes

### Case ID
ST-FUNC-001-004

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `init_huey()` returns a Huey instance backed by SQLite storage

### Preconditions
- `app/core/queue.py` module exists
- `HUEY_URL` points to a writable path
- `huey` package installed

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Set `HUEY_URL` to a temp file path | Variable set |
| 2 | Import `init_huey` from `app.core.queue` | Import succeeds |
| 3 | Call `init_huey()` | Returns Huey instance |
| 4 | Assert instance is of type `Huey` | Type check passes |
| 5 | Assert `huey.name == "demandflow"` | Instance name matches expected |

### Verification Points
- Huey instance created
- SQLite backend configured
- No HueyException raised

### Post-Conditions
- No persistent state changes; test environment restored

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_queue.py::TestInitHuey::test_init_huey_returns_instance

### Case ID
ST-FUNC-001-005

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `create_app()` uses default config when DATABASE_URL/HUEY_URL not set (no exception raised)

> Clarification: Per the feature design Boundary Decisions table, DATABASE_URL and
> HUEY_URL have default values. When unset, `create_app()` uses defaults and does
> NOT raise. The original ST spec assumed ConfigError — corrected to match real
> behavior (implementation is correct per Boundary table).

### Preconditions
- `DATABASE_URL` environment variable is not set
- `HUEY_URL` environment variable is not set
- Default config values exist in `app/core/config.py`

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Unset `DATABASE_URL` environment variable | Variable removed |
| 2 | Unset `HUEY_URL` environment variable | Variable removed |
| 3 | Import `create_app` from `app.main` | Import succeeds |
| 4 | Call `create_app()` | Returns FastAPI instance using default paths; no exception raised |
| 5 | Assert `app` is instance of `FastAPI` | Type check passes |
| 6 | Assert `app.title == "DemandFlow"` | Title matches expected string |

### Verification Points
- No exception raised when DATABASE_URL/HUEY_URL unset
- Default config values applied (sqlite:///data/demandflow.db, sqlite:///data/huey_queue.db)
- FastAPI instance returned with expected title

### Post-Conditions
- No persistent state changes; test environment restored

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_app.py::TestCreateApp::test_create_app_uses_default_config_when_not_set

### Case ID
ST-FUNC-001-006

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `get_db()` raises OSError when the SQLite path's parent is blocked by a regular file

> Clarification: When the SQLite path's parent is a regular file (not a directory),
> `get_db()` raises `OSError` (FileExistsError) at the mkdir step, NOT
> `OperationalError`. The original ST spec assumed OperationalError — corrected to
> match real behavior.

### Preconditions
- `DATABASE_URL` points to a path whose parent component is a regular file (not a directory)
- A regular file exists at the parent path location

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Create a regular file `blocker` in temp dir | File created |
| 2 | Set `DATABASE_URL` to `sqlite:///<blocker>/test.db` (parent is a file) | Variable set |
| 3 | Import `get_db` from `app.core.database` | Import succeeds |
| 4 | Call `next(get_db())` | Raises OSError (path blocked by a regular file) |

### Verification Points
- OSError raised when parent path is a regular file
- Error surfaces inability to create directory for SQLite file

### Post-Conditions
- No persistent state changes; test environment restored

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_database.py::TestGetDb::test_get_db_raises_on_unwritable_path

### Case ID
ST-FUNC-001-007

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `get_db()` session can execute a real query against SQLite and return data

### Preconditions
- SQLite database file is writable (temp directory)
- `DATABASE_URL` points to valid SQLite path

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Import `get_db` from `app.core.database` | Import succeeds |
| 2 | Get session via `next(get_db())` | Session created |
| 3 | Execute `session.execute(text("SELECT 1"))` | Returns result object |
| 4 | Assert `result.scalar() == 1` | Query returns expected value |
| 5 | Resume generator to trigger close | StopIteration; session closed |

### Verification Points
- Database connection established against real SQLite file
- Query execution returns expected scalar value
- Session lifecycle completes end-to-end

### Post-Conditions
- Session closed; temp database file left in temp directory

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_database.py::TestGetDbIntegration::test_get_db_session_executes_query

### Case ID
ST-FUNC-001-008

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `init_huey()` instance can enqueue a task to the real SQLite-backed Huey backend

### Preconditions
- Huey SQLite backend file is writable (temp directory)
- `HUEY_URL` points to a writable path
- Huey consumer not required for enqueue test

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Set `HUEY_URL` to a temp file path | Variable set |
| 2 | Import `init_huey` from `app.core.queue` | Import succeeds |
| 3 | Get Huey instance via `init_huey()` | Instance created |
| 4 | Define a dummy task: `@huey.task()` decorator on a function | Task registered |
| 5 | Enqueue task by calling the decorated function | Task enqueued; result object returned |
| 6 | Assert `huey.pending()` length >= 1 | Task reached the SQLite-backed queue |

### Verification Points
- Task enqueued successfully to real Huey backend
- Huey SQLite storage write operational
- No exceptions during enqueue

### Post-Conditions
- Temp Huey database file left in temp directory

### Metadata
- Category: FUNC
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_queue.py::TestInitHueyIntegration::test_init_huey_can_enqueue_task

### Case ID
ST-BNDRY-001-001

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `get_db()` auto-creates directory when DATABASE_URL points to a non-existent nested path

### Preconditions
- `DATABASE_URL` points to a nested path where parent directories do not exist
- Parent of the missing chain is writable

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Set `DATABASE_URL` to `sqlite:///<tmp>/nonexistent/deep/path/test.db` | Variable set |
| 2 | Import `get_db` from `app.core.database` | Import succeeds |
| 3 | Call `next(get_db())` | Returns Session instance |
| 4 | Assert the directory `<tmp>/nonexistent/deep/path/` exists | Directory auto-created |
| 5 | Resume generator to trigger close | StopIteration; session closed |

### Verification Points
- Missing directory chain auto-created (mkdir parents)
- No crash due to missing directory
- Session returned and usable

### Post-Conditions
- Auto-created directories and SQLite file remain in temp directory

### Metadata
- Category: BNDRY
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_database.py::TestGetDb::test_get_db_creates_directory_if_missing

### Case ID
ST-BNDRY-001-002

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `init_huey()` uses default SQLite path when HUEY_URL is an empty string

### Preconditions
- `HUEY_URL` environment variable set to empty string `""`
- Default Huey path is `sqlite:///data/huey_queue.db`

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Set `HUEY_URL=""` | Variable set to empty string |
| 2 | Import `init_huey` from `app.core.queue` | Import succeeds |
| 3 | Call `init_huey()` | Returns Huey instance |
| 4 | Assert instance is of type `Huey` | Type check passes |
| 5 | Assert `huey.storage.filename` ends with `huey_queue.db` | Default path used |

### Verification Points
- Empty string treated as "use default"
- Default SQLite backend path applied
- No exception for empty string input

### Post-Conditions
- Default Huey database file may be created in `data/` directory

### Metadata
- Category: BNDRY
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_queue.py::TestInitHuey::test_init_huey_uses_default_on_empty_string

### Case ID
ST-BNDRY-001-003

### Related Requirement
N/A (srs_trace empty — infrastructure feature)

### Test Objective
Verify `get_settings()` works without a .env file present (uses system environment variables)

### Preconditions
- `.env` file does not exist in project root (or is not loaded)
- System environment variables are set for required fields

### Test Steps

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | Unset `DATABASE_URL` and `HUEY_URL` (clean slate) | Variables removed |
| 2 | Set `DATABASE_URL=sqlite:///fallback.db` via system env | Variable set |
| 3 | Set `HUEY_URL=sqlite:///fallback_huey.db` via system env | Variable set |
| 4 | Import `get_settings` from `app.core.config` | Import succeeds |
| 5 | Call `get_settings()` | Returns Settings instance |
| 6 | Assert `settings.DATABASE_URL == "sqlite:///fallback.db"` | Field populated from system env |

### Verification Points
- Graceful handling of missing .env file
- System environment variables used as fallback
- No crash due to missing .env file

### Post-Conditions
- No persistent state changes; test environment restored

### Metadata
- Category: BNDRY
- Test Type: Real
- 已自动化: Yes
- Automated Test: tests/test_config.py::TestGetSettings::test_get_settings_works_without_dotenv

## Traceability Matrix

| Case ID | Requirement | Feature Design Row | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-001-001 | N/A | A | tests/test_app.py::TestCreateApp::test_create_app_returns_fastapi_instance | PASS |
| ST-FUNC-001-002 | N/A | B | tests/test_config.py::TestGetSettings::test_get_settings_loads_env_vars | PASS |
| ST-FUNC-001-003 | N/A | C | tests/test_database.py::TestGetDb::test_get_db_returns_session_and_closes | PASS |
| ST-FUNC-001-004 | N/A | D | tests/test_queue.py::TestInitHuey::test_init_huey_returns_instance | PASS |
| ST-FUNC-001-005 | N/A | E | tests/test_app.py::TestCreateApp::test_create_app_uses_default_config_when_not_set | PASS |
| ST-FUNC-001-006 | N/A | F | tests/test_database.py::TestGetDb::test_get_db_raises_on_unwritable_path | PASS |
| ST-FUNC-001-007 | N/A | J | tests/test_database.py::TestGetDbIntegration::test_get_db_session_executes_query | PASS |
| ST-FUNC-001-008 | N/A | K | tests/test_queue.py::TestInitHueyIntegration::test_init_huey_can_enqueue_task | PASS |
| ST-BNDRY-001-001 | N/A | G | tests/test_database.py::TestGetDb::test_get_db_creates_directory_if_missing | PASS |
| ST-BNDRY-001-002 | N/A | H | tests/test_queue.py::TestInitHuey::test_init_huey_uses_default_on_empty_string | PASS |
| ST-BNDRY-001-003 | N/A | I | tests/test_config.py::TestGetSettings::test_get_settings_works_without_dotenv | PASS |

## Real Test Case Execution Summary

| Metric | Value |
|--------|-------|
| Total Real Cases | 11 |
| Passed | 11 |
| Failed | 0 |
| Pending | 0 |

## Manual Test Case Summary

No manual test cases.
