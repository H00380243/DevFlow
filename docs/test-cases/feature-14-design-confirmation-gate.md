# Feature 14 — 设计确认门与迭代 — 验收测试用例

## 测试用例

### ST-FUNC-014-001: 设计确认成功
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 调用 handle_confirm(req_id, submitter_id) |
| 预期结果 | 状态变为 DESIGN_CONFIRMED → IN_IMPLEMENTATION；返回 new_status=IN_IMPLEMENTATION；push_fn 被调用通知提交人 |

### ST-FUNC-014-002: 设计驳回带原因
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, "需要修改") |
| 预期结果 | 状态变为 DESIGN_REJECTED → IN_DESIGN；返回 new_status=IN_DESIGN |

### ST-FUNC-014-003: 设计驳回空原因
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, "") |
| 预期结果 | 抛出 EmptyRejectReasonError；状态不变 |

### ST-FUNC-014-004: 设计驳回 None 原因
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, None) |
| 预期结果 | 抛出 EmptyRejectReasonError；状态不变 |

### ST-FUNC-014-005: 设计驳回空白原因
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, "   ") |
| 预期结果 | 抛出 EmptyRejectReasonError；状态不变 |

### ST-FUNC-014-006: 非提交人确认被拒绝
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM，提交人为 user001 |
| 步骤 | 1. 调用 handle_confirm(req_id, "other_user") |
| 预期结果 | 抛出 PermissionError；状态不变 |

### ST-FUNC-014-007: 非提交人驳回被拒绝
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 DESIGN_PENDING_CONFIRM，提交人为 user001 |
| 步骤 | 1. 调用 handle_reject(req_id, "other_user", "原因") |
| 预期结果 | 抛出 PermissionError；状态不变 |

### ST-FUNC-014-008: 错误状态确认
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态非 DESIGN_PENDING_CONFIRM（如 IN_DESIGN） |
| 步骤 | 1. 调用 handle_confirm(req_id, submitter_id) |
| 预期结果 | 抛出 InvalidTransitionError |

### ST-FUNC-014-009: 错误状态驳回
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态非 DESIGN_PENDING_CONFIRM（如 IN_DESIGN） |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, "原因") |
| 预期结果 | 抛出 InvalidTransitionError |

### ST-FUNC-014-010: 不存在的需求
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求 ID 不存在 |
| 步骤 | 1. 调用 handle_confirm("REQ-NONEXIST", "user001") |
| 预期结果 | 抛出 ValueError |

### ST-FUNC-014-011: 驳回推送重试失败
| 字段 | 值 |
|------|-----|
| 前置条件 | push_fn 持续抛出异常 |
| 步骤 | 1. push_fn 抛出 Exception |
| 预期结果 | NotificationFailedError 被记录；状态仍然正确变更 |

### ST-FUNC-014-012: 开始确认门（空起始）
| 字段 | 值 |
|------|-----|
| 前置条件 | 需求状态为 IN_DESIGN，设计产出物存在 |
| 步骤 | 1. 调用 complete_design(req_id) |
| 预期结果 | 状态变为 DESIGN_PENDING_CONFIRM（F013 集成） |

### ST-BNDRY-014-013: 第 4 次驳回终止
| 字段 | 值 |
|------|-----|
| 前置条件 | 已有 3 次 reject→retry→complete 周期 |
| 步骤 | 1. 第 4 次调用 handle_reject(req_id, submitter_id, "again") |
| 预期结果 | 状态变为 TERMINATED；通知管理员 |

### ST-BNDRY-014-014: 第 1 次超时（提醒）
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 DESIGN_PENDING_CONFIRM，已超 4h |
| 步骤 | 1. 调用 check_timeouts() |
| 预期结果 | 结果列表非空；escalated=False（仅提交人提醒） |

### ST-BNDRY-014-015: 首次驳回触发重设计
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, "修改") |
| 预期结果 | 状态变为 IN_DESIGN；design_team_fn 被调用 |

### ST-BNDRY-014-016: 超时恰好 4h 边界
| 字段 | 值 |
|------|-----|
| 前置条件 | updated_at = now - 4h |
| 步骤 | 1. 调用 check_timeouts(now) |
| 预期结果 | 该需求被包含在超时结果中（<= 判断） |

### ST-BNDRY-014-017: 双重点确认无效
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 DESIGN_CONFIRMED |
| 步骤 | 1. 调用 handle_confirm(req_id, submitter_id) |
| 预期结果 | 抛出 InvalidTransitionError |

### ST-BNDRY-014-018: 已终止需求驳回无效
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 TERMINATED |
| 步骤 | 1. 调用 handle_reject(req_id, submitter_id, "原因") |
| 预期结果 | 抛出 InvalidTransitionError |

### ST-INTG-014-019: 确认持久化
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. handle_confirm → 2. 新建 session 查询 |
| 预期结果 | DB 中 current_status = "IN_IMPLEMENTATION"；status_history 有 DESIGN_CONFIRM 记录 |

### ST-INTG-014-020: 驳回持久化
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. handle_reject → 2. 新建 session 查询 |
| 预期结果 | DB 中 current_status = "IN_DESIGN"；status_history 有 DESIGN_REJECT/DESIGN_RETRY 记录 |

### ST-INTG-014-021: 超时计数持久化
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态为 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 触发 TIMEOUT 事件 → 2. check_timeouts → 3. 新建 session 查询 |
| 预期结果 | status_history 至少有 2 条 TIMEOUT 记录（transition + check_timeouts） |

### ST-INTG-014-022: MAX_RETRY 持久化
| 字段 | 值 |
|------|-----|
| 前置条件 | 3 次 reject→retry→complete 周期 |
| 步骤 | 1. 第 4 次 reject → 2. 新建 session 查询 |
| 预期结果 | DB 中 current_status = "TERMINATED" |

### ST-INTG-014-023: 超时边界持久化
| 字段 | 值 |
|------|-----|
| 前置条件 | updated_at = now - 4h |
| 步骤 | 1. check_timeouts(now) → 2. 新建 session 查询 |
| 预期结果 | 需求被包含在结果中 |

### ST-INTG-014-024: 命令执行器路由确认
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 在 CommandExecutor.execute 中触发确认命令 |
| 预期结果 | 状态变为 IN_IMPLEMENTATION |

### ST-INTG-014-025: 命令执行器路由驳回
| 字段 | 值 |
|------|-----|
| 前置条件 | 状态 DESIGN_PENDING_CONFIRM |
| 步骤 | 1. 在 CommandExecutor.execute 中触发驳回命令 |
| 预期结果 | 状态变为 IN_DESIGN，且设计团重新被调用 |
