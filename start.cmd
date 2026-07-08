@echo off
cd /d "%~dp0"

echo ====================================
echo   DemandFlow - Starting Services
echo ====================================
echo.

echo [1/4] Cleanup ports 8000, 5173 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /F /PID %%a >nul 2>&1
echo   done
echo.

set LLM_API_KEY=sk-test-dummy
set LLM_BASE_URL=https://api.openai.com/v1
set LLM_MODEL_NAME=gpt-4
set IM_PLATFORM=feishu
set IM_WEBHOOK_SECRET=test-secret

echo [2/4] Init database ...
".venv\Scripts\python.exe" -c "from app.models import init_db; from sqlalchemy import create_engine; init_db(create_engine('sqlite:///data/demandflow.db'))"
if %ERRORLEVEL% neq 0 (
    echo FAILED
    pause
    exit /b 1
)
echo   done
echo.

echo [3/4] Start backend (port 8000)...
start "DemandFlow-Backend" /min ".venv\Scripts\uvicorn.exe" app.main:create_app --factory --reload --port 8000
echo   waiting for backend ...
timeout /t 5 /nobreak >nul
echo   done
echo.

echo [4/4] Start frontend (port 5173)...
start "DemandFlow-Frontend" cmd /c "cd /d frontend && npm run dev"
echo   waiting for frontend ...
timeout /t 4 /nobreak >nul
echo   done
echo.

start http://localhost:5173

echo ====================================
echo   All services started:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo.
echo   Press any key to stop all services...
echo ====================================
pause >nul

echo Stopping services ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /F /PID %%a >nul 2>&1
echo done.
pause
