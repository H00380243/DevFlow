# DemandFlow — Service Lifecycle Guide

> User-editable. Claude reads this file before managing services. Update when ports change or new services are added.

## Services

| Service Name | Port | Start Command | Stop Command | Verify URL |
|---|---|---|---|---|
| FastAPI API | 8000 | `uvicorn app.main:create_app --factory --reload --port 8000` | `kill $(lsof -ti :8000)` | `http://localhost:8000/api/dashboard/metrics` |
| Huey Worker | - | `huey consumer -k greenlet -w 2 demandflow.tasks` | `kill $(pgrep -f "huey consumer")` | - |
| React Dev Server | 5173 | `cd frontend && npm run dev` | `kill $(lsof -ti :5173)` | `http://localhost:5173` |

## Start All Services

### Unix/macOS
```bash
# FastAPI API
uvicorn demandflow.api:app --reload --port 8000 > /tmp/svc-api-start.log 2>&1 &
sleep 3
head -30 /tmp/svc-api-start.log

# Huey Worker
huey consumer -k greenlet -w 2 demandflow.tasks > /tmp/svc-worker-start.log 2>&1 &
sleep 3
head -30 /tmp/svc-worker-start.log

# React Dev Server
cd frontend && npm run dev > /tmp/svc-frontend-start.log 2>&1 &
sleep 3
head -30 /tmp/svc-frontend-start.log
```

### Windows
```bash
# FastAPI API
set LLM_API_KEY=sk-your-key& set LLM_BASE_URL=https://api.openai.com/v1& set LLM_MODEL_NAME=gpt-4& set IM_PLATFORM=feishu& set IM_WEBHOOK_SECRET=your-secret& uvicorn app.main:create_app --factory --reload --port 8000
timeout /t 3 /nobreak >nul
powershell "Get-Content $env:TEMP\svc-api-start.log -TotalCount 30"

# Huey Worker
cmd /c "start /b huey consumer -k greenlet -w 2 demandflow.tasks > %TEMP%\svc-worker-start.log 2>&1"
timeout /t 3 /nobreak >nul
powershell "Get-Content $env:TEMP\svc-worker-start.log -TotalCount 30"

# React Dev Server
cmd /c "start /b cd frontend && npm run dev > %TEMP%\svc-frontend-start.log 2>&1"
timeout /t 3 /nobreak >nul
powershell "Get-Content $env:TEMP\svc-frontend-start.log -TotalCount 30"
```

## Verify Services Running

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:5173
```

## Stop All Services

### Unix/macOS
```bash
# By PID (preferred)
kill <PID>

# By port (fallback)
lsof -ti :8000 | xargs kill -9
lsof -ti :5173 | xargs kill -9
```

### Windows
```bash
# By PID
taskkill /F /PID <PID>

# By port
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a
for /f "tokens=5" %a in ('netstat -ano ^| findstr :5173') do taskkill /F /PID %a
```

## Verify Services Stopped

```bash
# Unix/macOS
lsof -i :8000
lsof -i :5173

# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

## Restart Protocol

1. **Kill** — Stop All Services (by PID from task-progress.md, or by port)
2. **Verify dead** — run Verify Services Stopped; poll port max 5 seconds — must not respond
3. **Start** — run Start All Services with output capture → `head -30` → extract new PID/port → update task-progress.md
4. **Verify alive** — run Verify Services Running; poll health endpoint max 10 seconds — must respond
