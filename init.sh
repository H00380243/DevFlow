#!/bin/bash
# DemandFlow - Unix/macOS 初始化脚本
# 用法: bash init.sh

set -e

echo "========================================"
echo "DemandFlow 智能需求交付系统 - 初始化"
echo "========================================"
echo ""

# 检查 Python
echo "[1/6] 检查 Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "  ✗ Python 未安装或不在 PATH 中"
    echo "  请安装 Python 3.10+: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo "  ✓ Python: $PYTHON_VERSION"

# 创建虚拟环境
echo "[2/6] 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    echo "  ✓ 虚拟环境已创建"
else
    echo "  ✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "[3/6] 激活虚拟环境..."
source .venv/bin/activate
echo "  ✓ 虚拟环境已激活"

# 安装依赖
echo "[4/6] 安装后端依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "  ✓ 后端依赖已安装"
else
    echo "  ⚠ requirements.txt 不存在，跳过"
fi

echo "[5/6] 安装前端依赖..."
if [ -f "frontend/package.json" ]; then
    cd frontend
    npm install
    cd ..
    echo "  ✓ 前端依赖已安装"
else
    echo "  ⚠ frontend/package.json 不存在，跳过"
fi

# 验证工具
echo "[6/6] 验证工具..."
if command -v pytest &> /dev/null; then
    echo "  ✓ pytest: $(pytest --version)"
else
    echo "  ✗ pytest 未安装"
fi

if command -v mutmut &> /dev/null; then
    echo "  ✓ mutmut: $(mutmut --version)"
else
    echo "  ✗ mutmut 未安装"
fi

echo ""
echo "========================================"
echo "初始化完成！"
echo "========================================"
echo ""
echo "下一步："
echo "  1. 复制 .env.example 为 .env 并填写配置"
echo "  2. 运行 uvicorn demandflow.api:app --reload 启动后端"
echo "  3. 运行 cd frontend && npm run dev 启动前端"
