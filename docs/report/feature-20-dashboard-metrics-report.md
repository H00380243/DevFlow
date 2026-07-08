# F020 — 看板首页指标 Report

**Feature**: F020 — 看板首页指标  
**SRS Trace**: FR-018  
**Status**: PASS  
**Date**: 2026-07-09

---

## 1. Implementation Summary

| Artifact | Tests | Status |
|----------|-------|--------|
| `app/core/dashboard_service.py` | 10 pytest | ✅ |
| `app/main.py` (API route) | — | ✅ |
| `frontend/src/components/MetricCard.tsx` | 4 Vitest | ✅ |
| `frontend/src/pages/DashboardPage.tsx` | 4 Vitest | ✅ |

### Backend
- **`DashboardService.get_metrics()`**: Computes total_requirements, review_pass_rate (approved/total), in_progress_count via 3 SQLAlchemy queries
- **`GET /api/dashboard/metrics`**: FastAPI endpoint returning JSON

### Frontend
- **`MetricCard`**: Ant Design Card with label, value, loading skeleton, error badge
- **`DashboardPage`**: Fetches metrics on mount, renders 3 MetricCards or EmptyState
- **`ConfigProvider`**: Chinese locale for Ant Design components

---

## 2. Test Inventory (18 tests)

| ID | Category | Description | Tool | Result |
|----|----------|-------------|------|--------|
| A | FUNC/happy | Mixed statuses: 5 approved, 3 pending, 2 terminal → rate=50.0 | pytest | ✅ |
| B | FUNC/happy | Single REVIEW_APPROVED → rate=100.0 | pytest | ✅ |
| C | BNDRY/empty | Empty DB → total=0, rate=None, errors=[] | pytest | ✅ |
| D | BNDRY/edge | Single REJECTED → rate=0.0, in_progress=0 | pytest | ✅ |
| E | BNDRY/edge | 1000 all approved → rate=100.0 | pytest | ✅ |
| F | FUNC/error | DB connection fails → exception | pytest | ✅ |
| G | FUNC/error | Empty table → total=0, no error | pytest | ✅ |
| H | INTG/db | Real DB with 5 requirements → correct metrics | pytest | ✅ |
| I | BNDRY/edge | Single IN_IMPLEMENTATION → rate=100.0 exact | pytest | ✅ |
| J | FUNC/error | Partial query failure → errors present | pytest | ✅ |
| K | UI/render | DashboardPage title "总览" | Vitest | ✅ |
| L | UI/render | 3 MetricCards present | Vitest | ✅ |
| M | UI/render | MetricCard labels correct | Vitest | ✅ |
| N | UI/render | Metric values correct | Vitest | ✅ |
| O | UI/render | Null rate shows "--" | Vitest | ✅ |
| P | UI/render | Empty state when total=0 | Vitest | ✅ |
| Q | UI/render | Loading skeleton | Vitest | ✅ |
| R | UI/render | Error badge on partial failure | Vitest | ✅ |

---

## 3. Quality Gates

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Backend tests | — | 10 ✅ | ✅ |
| Frontend tests | — | 8 ✅ | ✅ |
| Total backend tests | — | 388 | ✅ |
| Total coverage | ≥95% | 95% | ✅ |

---

## 4. Files Changed

| File | Action |
|------|--------|
| `app/core/dashboard_service.py` | Created |
| `app/main.py` | Modified — added `/api/dashboard/metrics` route |
| `tests/test_dashboard_metrics.py` | Created — 10 tests |
| `frontend/` | Created — full Vite + React + Ant Design project |
| `frontend/src/components/MetricCard.tsx` | Created |
| `frontend/src/components/MetricCard.test.tsx` | Created |
| `frontend/src/pages/DashboardPage.tsx` | Created |
| `frontend/src/pages/DashboardPage.test.tsx` | Created |
| `frontend/src/App.tsx` | Created |
| `frontend/src/test-setup.ts` | Created |
| `frontend/vite.config.ts` | Created |
