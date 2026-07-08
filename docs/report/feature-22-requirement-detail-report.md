# F022 — 需求详情页 Report

**Feature**: F022 — 需求详情页  
**SRS Trace**: (none)  
**Status**: PASS  
**Date**: 2026-07-09

---

## 1. Implementation Summary

| Artifact | Tests | Status |
|----------|-------|--------|
| `app/core/requirement_detail_service.py` | 10 pytest | ✅ |
| `app/main.py` | — | ✅ (GET /api/requirements/{id}) |
| `frontend/src/pages/RequirementDetailPage.tsx` | 5 Vitest | ✅ |
| `frontend/src/pages/RequirementDetailPage.test.tsx` | — | ✅ |

### Backend
- **`RequirementDetailService.get_detail()`**: Fetches requirement with joined loads (review_results, design_results, implementation_results, status_history)
- **`GET /api/requirements/{id}`**: Returns full detail JSON with timeline sorted by triggered_at

### Frontend
- **`RequirementDetailPage`**: Left column (Descriptions with ID, summary, original text, submitter, scope, stage/status badges, tags, timestamps, counts) + Right column (Ant Design Timeline of status history)
- **Routing**: React Router — `/requirements/:id`
- **Error/loading/empty states**: Skeleton loading, Result error with back button, empty timeline message

---

## 2. Test Inventory (15 tests)

| ID | Category | Description | Tool | Result |
|----|----------|-------------|------|--------|
| T01 | FUNC/happy | Returns full info for existing req | pytest | ✅ |
| T02 | BNDRY/edge | Empty timeline when no history | pytest | ✅ |
| T03 | FUNC/happy | Timeline includes history entries | pytest | ✅ |
| T04 | FUNC/happy | Returns zero counts | pytest | ✅ |
| T05 | FUNC/error | Empty req_id raises ValueError | pytest | ✅ |
| T06 | FUNC/error | Nonexistent id raises LookupError | pytest | ✅ |
| T07 | FUNC/happy | Tags returned as list | pytest | ✅ |
| T08 | BNDRY/edge | Null tags returned as empty list | pytest | ✅ |
| T09 | FUNC/happy | created_at in ISO format | pytest | ✅ |
| T10 | FUNC/happy | Timeline sorted by triggered_at | pytest | ✅ |
| T11 | UI/render | Renders ID and summary | Vitest | ✅ |
| T12 | UI/render | Renders timeline component | Vitest | ✅ |
| T13 | UI/render | Renders tag items | Vitest | ✅ |
| T14 | UI/render | Renders stage/status badges | Vitest | ✅ |
| T15 | UI/render | Shows error state on fetch failure | Vitest | ✅ |

---

## 3. Files Changed

| File | Action |
|------|--------|
| `app/core/requirement_detail_service.py` | Created |
| `app/main.py` | Modified — added `/api/requirements/{id}` route |
| `tests/test_requirement_detail_service.py` | Created — 10 tests |
| `frontend/src/pages/RequirementDetailPage.tsx` | Created |
| `frontend/src/pages/RequirementDetailPage.test.tsx` | Created |
| `frontend/src/App.tsx` | Modified — added detail route |
