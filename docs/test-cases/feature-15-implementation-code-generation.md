# Feature 15 — 实施团代码生成 — 验收测试用例

## 测试用例

### ST-FUNC-015-001: 3 角色全部成功
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求处于 IN_IMPLEMENTATION 状态，存在 3 角色设计产出 |
| 步骤 | 1. 设置每个 agent.call_llm 返回有效代码文件 JSON → 2. 调用 run_implementation(req_id) |
| 预期结果 | CodeResult.code_files 包含 3 个文件；ImplementationResults 表有 1 行 |

### ST-FUNC-015-002: 歧义标注假设
| 字段 | 值 |
|------|-----|
| 前置条件 | LLM 返回含 ambiguity_notes 的 JSON |
| 步骤 | 1. agent.call_llm 返回含歧义标注 → 2. 调用 agent.generate(design_doc) |
| 预期结果 | CodeOutput.ambiguity_notes 非空，包含假设描述 |

### ST-FUNC-015-003: 全部 Agent 失败后重试耗尽
| 字段 | 值 |
|------|-----|
| 前置条件 | 3 个 agent.call_llm 全部持续抛出异常 |
| 步骤 | 1. 调用 run_implementation(req_id) |
| 预期结果 | AllAgentsFailedError 被抛出；_notify_agent_failure 被每个 agent 调用 |

### ST-FUNC-015-004: 重试后成功
| 字段 | 值 |
|------|-----|
| 前置条件 | agent.call_llm 前 2 次失败，第 3 次成功 |
| 步骤 | 1. 调用 retry_with_backoff(...) |
| 预期结果 | CodeOutput 返回；call_llm 恰好被调用 3 次 |

### ST-BNDRY-015-005: 代码文件为空
| 字段 | 值 |
|------|-----|
| 前置条件 | 3 个 agent 返回空 code_files |
| 步骤 | 1. 调用 run_implementation(req_id) |
| 预期结果 | CodeResult.code_files 为空列表；ImplementationResults 行创建，code_files=[] |

### ST-FUNC-015-006: 无设计产出错误
| 字段 | 值 |
|------|-----|
| 前置条件 | req_id 无 DesignResults 行 |
| 步骤 | 1. 调用 run_implementation(req_id) |
| 预期结果 | RequirementNotFoundError 抛出 |

### ST-FUNC-015-007: 需求不存在错误
| 字段 | 值 |
|------|-----|
| 前置条件 | req_id 在 requirements 表中不存在 |
| 步骤 | 1. 调用 run_implementation("NONEXISTENT") |
| 预期结果 | RequirementNotFoundError 抛出 |

### ST-BNDRY-015-008: 非 JSON 响应重试
| 字段 | 值 |
|------|-----|
| 前置条件 | agent.call_llm 返回非 JSON 文本 |
| 步骤 | 1. 调用 agent.generate(design_doc) |
| 预期结果 | CodeParseError 抛出 |

### ST-BNDRY-015-009: 部分 Agent 成功
| 字段 | 值 |
|------|-----|
| 前置条件 | 仅 1 个 agent 成功，其余 2 个返回 None |
| 步骤 | 1. 调用 run_implementation(req_id) |
| 预期结果 | CodeResult 包含唯一成功 agent 的文件 |

### ST-BNDRY-015-010: 代码文件去重
| 字段 | 值 |
|------|-----|
| 前置条件 | 3 个 agent 返回相同路径的文件 |
| 步骤 | 1. 调用 run_implementation(req_id) |
| 预期结果 | CodeResult.code_files 仅 1 行（最后写入者胜出） |

### ST-BNDRY-015-011: 缺失 code_files 键
| 字段 | 值 |
|------|-----|
| 前置条件 | LLM 返回 JSON 不含 code_files 键 |
| 步骤 | 1. 调用 agent.generate(design_doc) |
| 预期结果 | CodeParseError 抛出 |

### ST-BNDRY-015-012: 文件条目缺少 path/content
| 字段 | 值 |
|------|-----|
| 前置条件 | code_files 条目不含 path 或 content 字段 |
| 步骤 | 1. 调用 agent.generate(design_doc) |
| 预期结果 | CodeParseError 抛出 |

### ST-FUNC-015-013: 真实 _load_design_output 路径
| 字段 | 值 |
|------|-----|
| 前置条件 | 存在 3 角色设计产出 + 需求 |
| 步骤 | 1. 不 mock _load_design_output → 2. 设置 agent.call_llm → 3. run_implementation |
| 预期结果 | 完整堆栈执行：加载设计 → 并行生成 → 聚合 → 持久化 |

### ST-PERF-015-014: 并行执行性能
| 字段 | 值 |
|------|-----|
| 前置条件 | 3 个 agent 各执行 0.3s |
| 步骤 | 1. 调用 run_implementation(req_id) |
| 预期结果 | 总执行时间 < 0.9s（并行而非串行） |
