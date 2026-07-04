# DemandFlow - Windows 初始化脚本
# 用法: .\init.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DemandFlow 智能需求交付系统 - 初始化" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "[1/6] 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host "  请安装 Python 3.10+: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 创建虚拟环境
Write-Host "[2/6] 创建虚拟环境..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "  ✓ 虚拟环境已创建" -ForegroundColor Green
} else {
    Write-Host "  ✓ 虚拟环境已存在" -ForegroundColor Green
}

# 激活虚拟环境
Write-Host "[3/6] 激活虚拟环境..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "  ✓ 虚拟环境已激活" -ForegroundColor Green

# 安装依赖
Write-Host "[4/6] 安装后端依赖..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "  ✓ 后端依赖已安装" -ForegroundColor Green
} else {
    Write-Host "  ⚠ requirements.txt 不存在，跳过" -ForegroundColor Yellow
}

Write-Host "[5/6] 安装前端依赖..." -ForegroundColor Yellow
if (Test-Path "frontend\package.json") {
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "  ✓ 前端依赖已安装" -ForegroundColor Green
} else {
    Write-Host "  ⚠ frontend\package.json 不存在，跳过" -ForegroundColor Yellow
}

# 验证工具
Write-Host "[6/6] 验证工具..." -ForegroundColor Yellow
pytest --version 2>&1 | Out-Null
if ($?) {
    Write-Host "  ✓ pytest: $(pytest --version)" -ForegroundColor Green
} else {
    Write-Host "  ✗ pytest 未安装" -ForegroundColor Red
}

mutmut --version 2>&1 | Out-Null
if ($?) {
    Write-Host "  ✓ mutmut: $(mutmut --version)" -ForegroundColor Green
} else {
    Write-Host "  ✗ mutmut 未安装" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "初始化完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 复制 .env.example 为 .env 并填写配置" -ForegroundColor White
Write-Host "  2. 运行 uvicorn demandflow.api:app --reload 启动后端" -ForegroundColor White
Write-Host "  3. 运行 cd frontend && npm run dev 启动前端" -ForegroundColor White
