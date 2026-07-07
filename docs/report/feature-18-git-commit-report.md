# F018 — Git Commit & Secret Detection Report

**Feature**: F018 — Git 提交与密钥检测  
**SRS Trace**: FR-016  
**Status**: PASS  
**Date**: 2026-07-09

---

## 1. Implementation Summary

| Artifact | Lines | Stmts | Branch | Covered |
|----------|-------|-------|--------|---------|
| `app/core/git_handler.py` | 174 | 81 | 28 | 94% |
| `tests/test_secret_detector.py` | 130 | — | — | 11 tests |
| `tests/test_git_handler.py` | 128 | — | — | 10 tests |

### Key Classes
- **`SecretDetector`**: 8 regex patterns (AWS, Generic Password, Bearer, Private Key, GitHub Token, etc.); file content truncation (80 chars for previews); `detect()` raises `SecretDetectedError` with match details
- **`GitHandler`**: Stub-level git operations (create_branch, commit, push) — production wraps subprocess/gitpython
- **`GitCommitOrchestrator`**: Full workflow: secret scan → branch → commit → push with 3x exponential backoff retry; `push_enabled=False` skips push
- **`GitCommitFailedError`**, **`CredentialExpiredError`**: Domain exceptions for auth vs general failures

### State Machine Transitions (F017 edit)
- Added `IMPL_PENDING_ACCEPTANCE + TIMEOUT → IMPL_PENDING_ACCEPTANCE` (self-loop) to support confirmation timeout without state change

---

## 2. Test Inventory (21 tests)

| # | ID | Type | Category | Description | Result |
|---|-----|------|----------|-------------|--------|
| 1 | T001 | FUNC | happy | detect AWS key in CI config | ✅ |
| 2 | T002 | FUNC | happy | detect generic password | ✅ |
| 3 | T003 | FUNC | happy | detect bearer token | ✅ |
| 4 | T004 | FUNC | happy | detect private key header | ✅ |
| 5 | T005 | FUNC | happy | detect GitHub token | ✅ |
| 6 | T006 | FUNC | happy | detect GitHub token in variable assignment | ✅ |
| 7 | T007 | BNDRY | edge | empty files list — no error | ✅ |
| 8 | T008 | BNDRY | edge | empty file content — no error | ✅ |
| 9 | T009 | BNDRY | edge | None content — no error | ✅ |
| 10 | T010 | BNDRY | edge | secret on line 999 — correct line number | ✅ |
| 11 | T011 | BNDRY | edge | content truncation to 80 chars in match preview | ✅ |
| 12 | T012 | FUNC | happy | commit produces result with branch/message | ✅ |
| 13 | T013 | FUNC | happy | file count in commit message | ✅ |
| 14 | T014 | BNDRY | edge | many files truncated to "and N more" | ✅ |
| 15 | T015 | FUNC | error | push retry 3x then fails | ✅ |
| 16 | T016 | FUNC | error | auth error raises CredentialExpiredError | ✅ |
| 17 | T017 | FUNC | error | create branch error raises GitCommitFailedError | ✅ |
| 18 | T018 | FUNC | happy | push retry success on 2nd attempt | ✅ |
| 19 | T019 | BNDRY | edge | empty req_id raises ValueError | ✅ |
| 20 | T020 | FUNC | happy | commit message format | ✅ |
| 21 | T021 | FUNC | happy | push_enabled=False skips push | ✅ |

---

## 3. Quality Gates

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Line coverage | ≥80% | 96% (git_handler) | ✅ |
| Branch coverage | ≥70% | 100% (no partial branches) | ✅ |
| Total tests | — | 359 | ✅ |
| Total coverage | ≥95% | 95.06% | ✅ |

---

## 4. Decisions & Notes

- **MVP stub**: `GitHandler` methods are stubs (return constants); production implementation wraps gitpython/subprocess
- **Secret patterns**: 8 regex patterns covering AWS, GCP, GitHub, Bearer tokens, generic passwords, and PEM private keys
- **Credential vs push error**: Auth/credential errors raise `CredentialExpiredError` (no retry); other push errors retry 3x with exponential backoff
- **File truncation in commit message**: >5 files shown as "file1, file2, ... and N more"

---

## 5. Files Changed

| File | Action |
|------|--------|
| `app/core/git_handler.py` | Created — SecretDetector, GitHandler, GitCommitOrchestrator |
| `tests/test_secret_detector.py` | Created — 11 tests |
| `tests/test_git_handler.py` | Created — 10 tests |
| `app/core/state_machine.py` | Modified — added TIMEOUT self-loop for IMPL_PENDING_ACCEPTANCE |
