# F021 — 需求列表与筛选搜索 Report

**Feature**: F021 — 需求列表与筛选搜索  
**SRS Trace**: FR-019  
**Status**: PASS  
**Date**: 2026-07-09

---

## 1. Implementation Summary

| Artifact | Tests | Status |
|----------|-------|--------|
| `app/core/requirements_service.py` | 13 pytest | ✅ |
| `frontend/src/pages/RequirementsListPage.tsx` | 5 Vitest | ✅ |
| `frontend/src/pages/RequirementsListPage.test.tsx` | — | ✅ |

### Backend
- **`RequirementsService.get_requirements()`**: Paginated, filtered query with stage/status/submitter/search support
- **`GET /api/requirements`**: FastAPI endpoint with query params

### Frontend
- **`RequirementsListPage`**: Ant Design v6 Table with 6 columns, Select filters (stage/status), Input.Search, Pagination
- **Routing**: React Router v7 — `/` (Dashboard), `/requirements` (List)

---

## 2. Test Inventory (18 tests)

| ID | Category | Description | Tool | Result |
|----|----------|-------------|------|--------|
| T01 | FUNC/happy | Basic pagination — 5 items returned | pytest | ✅ |
| T02 | FUNC/happy | Page size 10 limits correctly | pytest | ✅ |
| T03 | BNDRY/edge | Second page of 15 items returns 5 | pytest | ✅ |
| T04 | BNDRY/edge | Page out of range returns empty | pytest | ✅ |
| T05 | FUNC/happy | Stage filter works | pytest | ✅ |
| T06 | FUNC/happy | Search by ID | pytest | ✅ |
| T07 | FUNC/happy | Search by summary | pytest | ✅ |
| T08 | BNDRY/edge | Empty search returns all | pytest | ✅ |
| T09 | FUNC/happy | Combined filters | pytest | ✅ |
| T10 | FUNC/error | Page=0 raises ValueError | pytest | ✅ |
| T11 | FUNC/error | Invalid page_size raises ValueError | pytest | ✅ |
| T12 | BNDRY/edge | Empty DB returns 0 total | pytest | ✅ |
| T13 | BNDRY/edge | Page size 50 at boundary | pytest | ✅ |
| T14 | UI/render | Page title "需求列表" | Vitest | ✅ |
| T15 | UI/render | Filter selectors present | Vitest | ✅ |
| T16 | UI/render | Table with 6 columns | Vitest | ✅ |
| T17 | UI/render | Pagination with >10 items | Vitest | ✅ |
| T18 | UI/render | Empty state when no results | Vitest | ✅ |

---

## 3. Quality Gates

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Backend tests | — | 13 | ✅ |
| Frontend tests | — | 5 | ✅ |
| Total backend tests | — | 401 | ✅ |

---

## 4. Files Changed

| File | Action |
|------|--------|
| `app/core/requirements_service.py` | Created |
| `app/main.py` | Modified — added `/api/requirements` route |
| `tests/test_requirements_service.py` | Created — 13 tests |
| `frontend/src/pages/RequirementsListPage.tsx` | Created |
| `frontend/src/pages/RequirementsListPage.test.tsx` | Created |
| `frontend/src/App.tsx` | Modified — added routing |
