# Feature Detailed Design: Git 提交与密钥检测 (Feature #18)

**Date**: 2026-07-09
**Feature**: #18 — Git 提交与密钥检测
**Priority**: high
**Dependencies**: [F017]
**Design Reference**: docs/plans/2026-07-04-demandflow-design.md § 2.4
**SRS Reference**: FR-016

## Context

F018 implements Git commit operations and pre-commit secret detection for DemandFlow. After code passes smoke verification (F016) and submitter confirms (F017), this feature creates a dedicated feature branch, commits code following Conventional Commits format, scans files for leaked secrets, and pushes to the remote repository — with retry logic and admin notification on failure.

## Design Alignment

### §2.4.2 Class Diagram (GitHandler & SecretDetector)

```mermaid
classDiagram
    class GitHandler {
        +create_branch(str req_id) str
        +commit(str branch, list~File~ files, str message) str
        +push(str branch)
    }

    class SecretDetector {
        +detect(list~File~) list~SecretMatch~
        -_scan_content(str content) list~SecretMatch~
        -_build_patterns() list~Pattern~
    }

    class SecretMatch {
        +str file_path
        +int line_number
        +str pattern_name
        +str matched_text
    }

    class GitCommitOrchestrator {
        +execute(str req_id, list~File~ files) GitCommitResult
        -_build_commit_message(str req_id, list~File~ files) str
        -_retry_push(str branch) None
    }

    class GitCommitResult {
        +str branch_name
        +str commit_id
        +str commit_message
    }

    GitCommitOrchestrator --> GitHandler
    GitCommitOrchestrator --> SecretDetector
    GitHandler ..> SecretMatch : raises SecretDetectedError
```

- **Key classes**: `GitHandler` (branch/commit/push), `SecretDetector` (regex scanning), `GitCommitOrchestrator` (workflow orchestration), `SecretMatch` (detection result), `GitCommitResult` (commit output)
- **Interaction flow**: `GitCommitOrchestrator.execute()` → secret scan → create branch → commit → push
- **Third-party deps**: `gitpython ^3.1` (Git operations via subprocess/Python bindings)
- **Deviations**: none

## SRS Requirement

### FR-016: Git 提交

**Priority**: Must
**EARS**: When 实施结果经提交人确认，the system shall 自动将代码提交到指定 Git 仓库的独立分支并生成规范 Commit 信息。
**Visual output**: 看板详情展示 Git 提交记录
**Acceptance Criteria**:
- **AC-1**: Given 实施确认，when 提交，then 创建独立分支并提交代码 + 符合 Conventional Commits 规范的 Commit 信息
- **AC-2**: Given Git 提交失败，when 处理，then 重试 3 次后 IM 通知管理员
- **AC-3**: Given 代码含疑似密钥（API Key/密码/Token 模式），when 提交前，then 阻止提交并 IM 告警提交人
- **AC-4**: Given 指定仓库写入凭证失效，when 提交，then IM 通知管理员检查凭证

## Component Data-Flow Diagram

```mermaid
graph TD
    A[GitCommitOrchestrator.execute] -->|list~File~| B[SecretDetector.detect]
    B -->|SecretMatch[]| C{Secrets found?}
    C -->|Yes| D[raise SecretDetectedError]
    C -->|No| E[GitHandler.create_branch]
    E -->|branch_name| F[GitHandler.commit]
    F -->|commit_id| G[GitHandler.push]
    G -->|OK| H[GitCommitResult]
    G -->|AuthError| I[raise CredentialExpiredError]
    G -->|GitError| J[retry up to 3x]
    J -->|exhausted| K[raise GitCommitFailedError]

    style D fill:#f66,color:#fff
    style I fill:#f66,color:#fff
    style K fill:#f66,color:#fff
```

## Interface Contract

| Method | Signature | Preconditions | Postconditions | Raises |
|--------|-----------|---------------|----------------|--------|
| `create_branch` | `create_branch(req_id: str) -> str` | Git repo initialized; req_id format valid | Returns branch name `feature/{req_id}`; branch created and checked out | `GitOperationError` — git clone/checkout fails |
| `commit` | `commit(branch: str, files: list[dict], message: str) -> str` | Branch exists and is checked out; files list non-empty | Returns commit SHA; all files staged and committed with `message` | `GitOperationError` — git add/commit fails |
| `push` | `push(branch: str) -> None` | Branch has at least one commit; remote configured | Branch pushed to remote | `GitOperationError` — network/permission failure |
| `detect` | `detect(files: list[dict]) -> list[dict]` | files list provided (may be empty) | Returns list of SecretMatch dicts; empty list if no secrets found | `SecretDetectedError` — one or more secrets found (raises with matches list) |
| `execute` | `execute(req_id: str, files: list[dict], push_enabled: bool = True) -> dict` | State is IMPL_APPROVED; files non-empty | Returns `GitCommitResult` dict; code committed to remote | `SecretDetectedError`, `GitCommitFailedError`, `CredentialExpiredError` |
| `build_commit_message` | `_build_commit_message(req_id: str, files: list[dict]) -> str` | files list provided | Returns string in Conventional Commits format: `feat({req_id}): auto-generated commit\n\nFiles: {count} files changed` | N/A — pure computation |

**Design rationale**:
- **Commit message format**: `feat({req_id}): auto-generated commit` with file count in body — aligns with Conventional Commits `type(scope): description` convention; scope uses req_id for traceability
- **Secret detection BEFORE branch creation**: scan happens first to avoid creating empty/abandoned branches on detection failure
- **`push_enabled` flag**: allows unit testing the commit flow without actual push; also supports offline/CI scenarios
- **3x retry on push**: matches SRS AC-2 "重试 3 次" requirement; uses exponential backoff (1s, 2s, 4s)

## Visual Rendering Contract

> N/A — backend-only feature, no visual output (`"ui": false`)

## Internal Sequence Diagram

```mermaid
sequenceDiagram
    participant ORCH as GitCommitOrchestrator
    participant SD as SecretDetector
    participant GH as GitHandler
    participant GIT as GitPython/CLI
    participant DB as SQLite

    ORCH->>SD: detect(files)
    alt Secrets found
        SD-->>ORCH: SecretDetectedError(matches)
        ORCH-->>ORCH: raise SecretDetectedError
    else Clean
        SD-->>ORCH: []
    end

    ORCH->>GH: create_branch(req_id)
    GH->>GIT: git checkout -b feature/{req_id}
    GIT-->>GH: OK
    GH-->>ORCH: branch_name

    ORCH->>GH: commit(branch, files, message)
    GH->>GIT: git add + git commit
    GIT-->>GH: commit_sha
    GH-->>ORCH: commit_id

    ORCH->>GH: push(branch)
    alt Auth failure
        GH-->>ORCH: CredentialExpiredError
        ORCH-->>ORCH: raise CredentialExpiredError
    else Network error (retryable)
        GH-->>ORCH: GitOperationError
        ORCH->>GH: push(branch) [retry 1]
        GH-->>ORCH: GitOperationError
        ORCH->>GH: push(branch) [retry 2]
        GH-->>ORCH: GitOperationError
        ORCH->>GH: push(branch) [retry 3]
        GH-->>ORCH: GitOperationError
        ORCH-->>ORCH: raise GitCommitFailedError
    else Success
        GH-->>ORCH: None
    end

    ORCH-->>ORCH: return GitCommitResult
```

## Algorithm / Core Logic

### SecretDetector.detect

#### Flow Diagram

```mermaid
flowchart TD
    A[Start: files list] --> B{files empty?}
    B -->|Yes| C[Return empty list]
    B -->|No| D[Initialize matches list]
    D --> E[For each file]
    E --> F[Split content by lines]
    F --> G[For each line]
    G --> H[For each pattern]
    H --> I{re.search pattern on line}
    I -->|Match| J[Append SecretMatch]
    I -->|No match| K[Continue]
    J --> K
    K --> H
    H -->|All patterns done| G
    G -->|All lines done| E
    E -->|All files done| L{matches empty?}
    L -->|Yes| M[Return empty list]
    L -->|No| N[raise SecretDetectedError with matches]
```

#### Pseudocode

```
SECRET_PATTERNS = [
    ("AWS Access Key", r"AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key", r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"),
    ("Generic API Key", r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    ("Generic Password", r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    ("Bearer Token", r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}"),
    ("Private Key", r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    ("GitHub Token", r"ghp_[A-Za-z0-9]{36}"),
    ("Slack Token", r"xox[bpsar]-[0-9a-zA-Z\-]{10,}"),
]

FUNCTION detect(files: list[dict]) -> list[dict]
    matches = []
    FOR file IN files:
        content = file["content"]
        path = file["path"]
        lines = content.split("\n")
        FOR line_num, line IN enumerate(lines, 1):
            FOR name, pattern IN SECRET_PATTERNS:
                IF re.search(pattern, line):
                    matches.append(SecretMatch(
                        file_path=path,
                        line_number=line_num,
                        pattern_name=name,
                        matched_text=line.strip()[:80]
                    ))
    IF matches is NOT empty:
        RAISE SecretDetectedError(matches)
    RETURN []
END
```

#### Boundary Decisions

| Parameter | Min | Max | Empty/Null | At boundary |
|-----------|-----|-----|------------|-------------|
| files | 0 | unlimited | returns [] (no scan) | empty → no-op |
| file.content | "" | unlimited | skip empty files | empty → no lines to scan |
| file.path | "" | unlimited | include in match with empty path | empty → still reported |
| line_number | 1 | N/A | N/A | starts at 1 (human-readable) |
| matched_text | 1 char | 80 chars | N/A | truncated at 80 chars to avoid log overflow |

#### Error Handling

| Condition | Detection | Response | Recovery |
|-----------|-----------|----------|----------|
| File content is None | `file["content"]` raises TypeError | Skip file, log warning | Caller provides valid content |
| Invalid regex pattern | re.search raises re.error | Skip pattern, log error | Fix pattern definition |

### GitHandler.create_branch / commit / push

#### Flow Diagram (push with retry)

```mermaid
flowchart TD
    A[Start: push branch] --> B[attempt = 0]
    B --> C{attempt < 3?}
    C -->|Yes| D[try git push]
    D -->|AuthError| E[raise CredentialExpiredError]
    D -->|Success| F[Return None]
    D -->|Other GitError| G[attempt += 1, sleep 2^attempt]
    G --> C
    C -->|No| H[raise GitCommitFailedError]
```

#### Pseudocode

```
FUNCTION push(branch: str) -> None
    attempt = 0
    WHILE attempt < 3:
        TRY:
            repo = Git(repo_path)
            repo.remote().push(branch)
            RETURN
        EXCEPT AuthenticationError:
            RAISE CredentialExpiredError(branch)
        EXCEPT GitError as e:
            attempt += 1
            IF attempt < 3:
                sleep(2 ** attempt)
            ELSE:
                RAISE GitCommitFailedError(branch, e)
    END
END
```

#### Boundary Decisions

| Parameter | Min | Max | Empty/Null | At boundary |
|-----------|-----|-----|------------|-------------|
| branch | 1 char | 255 chars | N/A | non-empty required |
| files | 1 file | unlimited | N/A | non-empty required for commit |
| retry count | 0 | 3 | N/A | stops after 3 attempts |
| retry delay | 1s | 4s | N/A | exponential: 1s, 2s, 4s |

#### Error Handling

| Condition | Detection | Response | Recovery |
|-----------|-----------|----------|----------|
| Authentication failure | `git.exc.GitCommandError` with auth stderr | `CredentialExpiredError` | Caller notifies admin |
| Network timeout | `git.exc.GitCommandError` with timeout stderr | Retry up to 3x | Automatic retry |
| Branch not found | `git.exc.GitCommandError` with "not found" | `GitOperationError` | Caller retries create_branch |
| Remote not configured | `git.exc.GitCommandError` with "remote" | `GitOperationError` | Admin configures remote |
| Empty file list | Check `len(files) == 0` | `ValueError` | Caller provides files |

### GitCommitOrchestrator.execute

#### Flow Diagram

```mermaid
flowchart TD
    A[Start: execute] --> B[SecretDetector.detect files]
    B -->|SecretDetectedError| C[raise SecretDetectedError]
    B -->|Clean| D[GitHandler.create_branch req_id]
    D -->|Error| E[raise GitCommitFailedError]
    D -->|OK branch_name| F[GitHandler.commit branch, files, message]
    F -->|Error| E
    F -->|OK commit_id| G{push_enabled?}
    G -->|Yes| H[GitHandler.push branch with retry]
    H -->|CredentialExpiredError| I[raise CredentialExpiredError]
    H -->|GitCommitFailedError| J[raise GitCommitFailedError]
    H -->|OK| K[return GitCommitResult]
    G -->|No| K
```

#### Pseudocode

```
FUNCTION execute(req_id: str, files: list[dict], push_enabled: bool = True) -> dict
    // Step 1: Secret detection
    matches = SecretDetector.detect(files)  // raises SecretDetectedError if found

    // Step 2: Create branch
    branch_name = f"feature/{req_id}"
    GitHandler.create_branch(req_id)

    // Step 3: Build commit message
    message = _build_commit_message(req_id, files)

    // Step 4: Commit
    commit_id = GitHandler.commit(branch_name, files, message)

    // Step 5: Push (if enabled)
    IF push_enabled:
        GitHandler.push(branch_name)

    RETURN GitCommitResult(branch_name, commit_id, message)
END

FUNCTION _build_commit_message(req_id: str, files: list[dict]) -> str
    file_count = len(files)
    paths = [f["path"] for f in files[:5]]  // first 5 for brevity
    paths_str = "\n".join(f"  - {p}" for p in paths)
    suffix = f"\n  ... and {file_count - 5} more" IF file_count > 5 ELSE ""
    RETURN f"feat({req_id}): auto-generated implementation\n\nFiles changed ({file_count}):\n{paths_str}{suffix}"
END
```

#### Boundary Decisions

| Parameter | Min | Max | Empty/Null | At boundary |
|-----------|-----|-----|------------|-------------|
| req_id | "REQ-YYYYMMDD-NNN" | same | N/A | validated by DB constraint |
| files | 1 | unlimited | N/A | non-empty enforced |
| push_enabled | True | False | N/A | False for unit tests |

#### Error Handling

| Condition | Detection | Response | Recovery |
|-----------|-----------|----------|----------|
| Secret detected | `SecretDetectedError` raised | Abort commit; notify submitter with match details | Remove secrets, re-submit |
| Branch creation fails | `GitOperationError` from create_branch | Abort; raise `GitCommitFailedError` | Check repo access |
| Commit fails | `GitOperationError` from commit | Abort; raise `GitCommitFailedError` | Check file permissions |
| Push auth failure | `CredentialExpiredError` from push | Raise `CredentialExpiredError` | Admin refreshes credentials |
| Push network failure | `GitOperationError` from push after 3 retries | Raise `GitCommitFailedError` | Check network; retry later |

## State Diagram

> N/A — stateless feature; Git operations are fire-and-forget side effects. The state machine transition (IMPL_APPROVED → DELIVERED via IMPL_CONFIRM) is handled by F007/F017, not by this feature. GitHandler is called as a side effect within that transition.

## Test Inventory

| ID | Category | Traces To | Input / Setup | Expected | Kills Which Bug? |
|----|----------|-----------|---------------|----------|-----------------|
| A | FUNC/happy | FR-016 AC-1 | req_id="REQ-20260709-001", files=[{path:"a.py",content:"x=1"}] | GitCommitResult with branch="feature/REQ-20260709-001", commit_id non-empty, message starts with "feat(" | No commit produced |
| B | FUNC/happy | FR-016 AC-1 | files=[{path:"a.py",content:"x=1"},{path:"b.py",content:"y=2"}] | commit_message contains "2" (file count) | File count missing |
| C | FUNC/happy | FR-016 AC-1 | files=[{path:f"f{i}.py",content:str(i)} for i in range(10)] | commit_message contains "... and 5 more" | Truncation not applied |
| D | FUNC/error | FR-016 AC-2 | Mock git push to raise GitError 3 times | GitCommitFailedError raised after 3 attempts | No retry logic |
| E | FUNC/error | FR-016 AC-4 | Mock git push to raise AuthenticationError | CredentialExpiredError raised immediately | Auth not detected |
| F | FUNC/error | FR-016 AC-3 | files=[{path:"config.py",content:'API_KEY="AKIA12345678901234567890"'}] | SecretDetectedError with pattern_name="AWS Access Key" | Secret detection disabled |
| G | FUNC/error | FR-016 AC-3 | files=[{path:".env",content:'password="supersecret123"'}] | SecretDetectedError with pattern_name="Generic Password" | Password pattern missing |
| H | FUNC/error | FR-016 AC-3 | files=[{path:"auth.py",content:'bearer eyJhbGciOiJIUzI1NiJ9.test.signature'}] | SecretDetectedError with pattern_name="Bearer Token" | Bearer token not detected |
| I | FUNC/error | FR-016 AC-3 | files=[{path:"key.pem",content:"-----BEGIN RSA PRIVATE KEY-----\nMIIE..."}] | SecretDetectedError with pattern_name="Private Key" | Private key not detected |
| J | FUNC/error | FR-016 AC-3 | files=[{path:"ci.yml",content:'GITHUB_TOKEN: "ghp_abcdefghijklmnopqrstuvwxyz1234567890"'}] | SecretDetectedError with pattern_name="GitHub Token" | GitHub token not detected |
| K | BNDRY/edge | §5 Boundary | files=[] | ValueError or empty list returned (no scan) | Crash on empty input |
| L | BNDRY/edge | §5 Boundary | files=[{path:"empty.py",content:""}] | No secrets detected, empty file skipped | Crash on empty content |
| M | BNDRY/edge | §5 Boundary | files=[{path:"a.py",content:None}] | TypeError caught, file skipped | Crash on None content |
| N | BNDRY/edge | §5 Boundary | files with 1000 lines, 1 secret on line 999 | SecretDetectedError with line_number=999 | Off-by-one in line counting |
| O | BNDRY/edge | §5 Boundary | matched_text longer than 80 chars | matched_text truncated to 80 chars | Log overflow |
| P | FUNC/error | §5 Error Handling | Mock git remote().push to fail on 1st/2nd, succeed on 3rd | Push succeeds after 2 retries | No exponential backoff |
| Q | FUNC/error | §3 Interface Contract | req_id="" (empty string) | ValueError or GitOperationError | Empty req_id accepted |
| R | SEC/detect | FR-016 AC-3 | files=[{path:"a.py",content:'github_token = "ghp_abcdefghijklmnopqrstuvwx"'}] | SecretDetectedError with pattern_name="GitHub Token" | GitHub token pattern missing |
| S | FUNC/happy | §5 _build_commit_message | req_id="REQ-20260709-001", 1 file | message starts with "feat(REQ-20260709-001): auto-generated implementation" | Wrong commit format |
| T | FUNC/error | §3 Interface Contract | Mock create_branch raises GitOperationError | GitCommitFailedError propagated | Error swallowed silently |

**INTG: N/A** — Git operations are mocked for unit testing; no real Git repo integration in unit tests.

**Design Interface Coverage Gate**:
- `create_branch` — Row A, D, T
- `commit` — Row A, B, C
- `push` — Row D, E, P
- `detect` — Row F, G, H, I, J, K, L, M, N, O, R
- `execute` — Row A, D, E, F, K, Q
- `_build_commit_message` — Row A, B, C, S

All 6 public methods have ≥1 test row. ✓

## Tasks

### Task 1: Write failing tests
**Files**: `tests/test_git_handler.py`, `tests/test_secret_detector.py`
**Steps**:
1. Create `tests/test_secret_detector.py` with imports (`pytest`, `re`, `app.core.git_handler.SecretDetector`, `SecretDetectedError`)
2. Write tests for SecretDetector: test F (AWS key), G (password), H (bearer), I (private key), J (GitHub token), R (GitHub token in var), K (empty files), L (empty content), M (None content), N (line 999), O (truncation)
3. Create `tests/test_git_handler.py` with imports (`pytest`, `unittest.mock`, `app.core.git_handler.GitHandler`, `GitCommitOrchestrator`, `GitCommitResult`)
4. Write tests for GitHandler: test A, B, C (happy path commit), D (retry 3x), E (auth error), P (retry success), Q (empty req_id), T (create_branch error)
5. Run: `pytest tests/test_secret_detector.py tests/test_git_handler.py -v`
6. **Expected**: All tests FAIL — modules don't exist yet

### Task 2: Implement minimal code
**Files**: `app/core/git_handler.py`
**Steps**:
1. Create `app/core/git_handler.py` with `SecretDetector` class implementing `detect()` per §5 pseudocode (SECRET_PATTERNS list, regex scan, SecretDetectedError)
2. Implement `SecretMatch` Pydantic model with file_path, line_number, pattern_name, matched_text
3. Implement `GitHandler` class with `create_branch()`, `commit()`, `push()` per §5 pseudocode
4. Implement `GitCommitOrchestrator` with `execute()` and `_build_commit_message()` per §5
5. Implement retry logic with exponential backoff in `push()` per §5
6. Run: `pytest tests/test_secret_detector.py tests/test_git_handler.py -v`
7. **Expected**: All tests PASS

### Task 3: Coverage Gate
1. Run: `pytest tests/test_secret_detector.py tests/test_git_handler.py --cov=app/core/git_handler --cov-branch --cov-report=term-missing`
2. Check: line ≥80%, branch ≥70%. If below: return to Task 1.
3. Record coverage output as evidence.

### Task 4: Refactor
1. Extract SECRET_PATTERNS to module-level constant for reusability
2. Add type hints to all public methods
3. Ensure all exceptions inherit from a common `GitError` base class
4. Run full test suite: `pytest tests/ -v`

### Task 5: Mutation Gate
1. Manual mutation testing: mutate each regex pattern (remove one char), verify test catches
2. Mutate retry counter (change 3→0), verify test D catches
3. Mutate commit message format, verify test S catches
4. Record mutation results as evidence.

## Verification Checklist
- [x] All SRS acceptance criteria (from srs_trace FR-016) traced to Interface Contract postconditions — AC-1→create_branch+commit, AC-2→push retry, AC-3→detect, AC-4→push auth
- [x] All SRS acceptance criteria traced to Test Inventory rows — AC-1→A/B/C, AC-2→D, AC-3→F/G/H/I/J/R, AC-4→E
- [x] Algorithm pseudocode covers all non-trivial methods — detect, push retry, execute, _build_commit_message
- [x] Boundary table covers all algorithm parameters — files, content, branch, retry count, matched_text
- [x] Error handling table covers all Raises entries — GitOperationError, SecretDetectedError, GitCommitFailedError, CredentialExpiredError
- [x] Test Inventory negative ratio >= 40% — 13 negative/edge tests out of 20 total = 65%
- [x] Visual Rendering Contract complete for ui:false features — N/A
- [x] Each skipped section has explicit "N/A — [reason]"
- [x] Every section (§2-§6) complete or N/A justified

## Clarification Addendum

> Assumptions made — all low-impact, no design signature changes required.

| # | Category | Original Assumption | Rationale | Authority |
|---|----------|--------------------|-----------|-----------|
| 1 | SRS-VAGUE | "Conventional Commits 规范" → format is `feat({req_id}): auto-generated implementation` | Standard Conventional Commits spec defines `type(scope): description`; req_id serves as scope for traceability | assumed |
| 2 | SRS-VAGUE | "疑似密钥" → 8 regex patterns (AWS key/secret, generic API key, generic password, bearer token, private key, GitHub token, Slack token) | Industry-standard patterns from gitleaks/secret-scanning tools; covers common credential formats | assumed |
| 3 | SRS-VAGUE | "凭证失效" → detected via git AuthenticationError exception from gitpython | Git credential errors surface as authentication failures in gitpython; no separate credential check needed | assumed |
| 4 | SRS-VAGUE | "重试 3 次后 IM 通知管理员" → retry applies to push only; create_branch/commit failures abort immediately | Push is the most common failure point (network); branch/commit failures indicate config issues requiring admin attention | assumed |
| 5 | NFR-GAP | NFR not explicitly referenced; all thresholds derived from FR-016 ACs | No standalone NFR for git operations performance | assumed |
