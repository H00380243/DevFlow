# F015 实施团代码生成 — 报告

## 基本信息
- **特征 ID**: F015
- **标题**: 实施团代码生成
- **优先级**: high
- **SRS 追踪**: FR-013
- **依赖**: F007 ✓ (状态机引擎)

## 实现摘要
实现实施团 3 角色并行代码生成，遵循 F012 设计团模式。

### 核心组件
- **ImplementationAgent**: 3 角色（后端开发/前端开发/质量保障），生成 CodeOutput
  - `generate(design_doc)`: 构建 Prompt → call_llm → 解析 JSON → CodeOutput
  - `_build_prompt(design_doc)`: 格式化 Prompt 模板（含设计文档信息）
  - 错误处理: `LLMCallError`(LLM 失败), `CodeParseError`(JSON 解析/字段缺失)
- **ImplementationTeam**: 协调器，ThreadPoolExecutor 并行执行 3 Agent
  - `run_implementation(req_id)`: 加载设计产出 → 并行执行 → 聚合 → 持久化 → CodeResult
  - `_load_design_output(req_id)`: 加载 DesignResults 最新版本，组装设计文档 dict
  - `_aggregate_results`: 文件去重（按路径，后写入者胜出）+ 歧义标注合并
  - `_persist_output`: 保存到 ImplementationResults 表
- **retry_with_backoff**: 复用 F008 指数退避模式（3 次），支持 CodeParseError/LLMCallError

### 模型
- `CodeOutput`: agent_role, raw_text, code_files[], ambiguity_notes[]
- `CodeResult`: requirement_id, code_files[], ambiguity_notes[]

### 关键设计决策
- 状态流转不在 F015 处理（IN_IMPLEMENTATION → IMPL_PENDING_ACCEPTANCE 由 F016 触发）
- 代码文件按路径去重（多角色可能产生相同文件，后写入者胜出）
- `_load_design_output` 读取 DesignResults 内存组装，无需 MinIO

## TDD 结果
- **测试总数**: 17（12 设计清单 + 5 补充）
- **负面比例**: 9/17 = 53%
- **测试类别**: FUNC(7), BNDRY(6), PERF(1), INTG(3)

## 覆盖率
- `implementation_team.py`: 91% line, branch threshold met（阈值 80% ✅）
- 总体: 95% line

## 风险
- ⚠ [Coverage] `generate()` 的 LLMCallError 抛出路径和部分 `_load_design_output` 分支未完全覆盖（剩余 9 个 miss）
- ⚠ [Design] `retry_with_backoff` 为 F015 本地重定义（非直接复用 F008）；后续检查是否需要统一

## Git
- SHA: 待定
- 消息: feat(F015): 实施团代码生成 — ImplementationTeam, 17 tests, 91% line
