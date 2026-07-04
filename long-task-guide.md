# DemandFlow — Worker Session Guide

## Environment Commands

### 环境激活
```bash
# Unix/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 测试执行
```bash
# 后端测试
pytest tests/ -v --cov=demandflow --cov-report=html

# 前端测试
cd frontend && npm run test
```

### 变异测试
```bash
# Python 变异测试
mutmut run --paths-to-mutate=demandflow/
```

### 覆盖率报告
```bash
# 生成 HTML 报告
pytest tests/ --cov=demandflow --cov-report=html
open htmlcov/index.html
```

## Service Commands

### 启动后端服务
```bash
# 启动 FastAPI
uvicorn demandflow.api:app --reload --port 8000

# 启动 Huey Worker（另一个终端）
huey consumer -k greenlet -w 2 demandflow.tasks
```

### 启动前端服务
```bash
cd frontend && npm run dev
```

### 健康检查
```bash
curl http://localhost:8000/health
```

## Config Management

项目使用 `.env` 文件管理环境变量：

1. 复制 `.env.example` 为 `.env`
2. 填写必要的配置值
3. 重启服务使配置生效

Worker Config Gate 会在检测到缺失配置时提示用户。

## Real Test Convention

### 测试识别
- **Marker**: `@pytest.mark.real` 标记真实测试
- **Mock 模式**: `mock` 或 `Mock` 关键字标识 mock 测试

### 运行真实测试
```bash
pytest tests/ -m real -v
```

### 示例真实测试
```python
import pytest

@pytest.mark.real
def test_submit_requirement():
    """测试需求提交流程（无 mock）"""
    # Given: 用户发送需求消息
    # When: 系统处理消息
    # Then: 生成需求 ID
    pass
```

## Critical Rules

1. **TDD 严格遵循**: Red → Green → Refactor → Coverage → Mutation
2. **质量门禁**: 行覆盖率 ≥ 80%，分支覆盖率 ≥ 70%，变异得分 ≥ 75%
3. **状态机安全**: 每次状态流转必须持久化到 SQLite
4. **IM 同步**: 看板操作必须同步 IM 通知
5. **密钥检测**: Git 提交前必须扫描密钥
