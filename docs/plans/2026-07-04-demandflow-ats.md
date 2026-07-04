# DemandFlow 智能需求交付系统 — Acceptance Test Strategy

**Date**: 2026-07-04
**Status**: Approved
**SRS Reference**: docs/plans/2026-07-04-demandflow-srs.md
**Design Reference**: docs/plans/2026-07-04-demandflow-design.md
**UCD Reference**: docs/plans/2026-07-04-demandflow-ucd.md

## 1. Scope

### 1.1 项目规模

- **FR 需求**: 21 个（FR-001 ~ FR-021）
- **NFR 需求**: 11 个（NFR-001 ~ NFR-011）
- **IFR 需求**: 4 个（IFR-001 ~ IFR-005）
- **Features**: 23 个（F001 ~ F023）
- **项目规模**: Small → 完整 ATS 文档

### 1.2 ATS 目的

为每个需求映射验收场景与测试类别，约束下游 feature-st 的测试用例推导，确保：
- 类别均衡（避免 FUNC/BNDRY 过重，SEC/PERF/UI 缺失）
- NFR 测试方法预先定义
- 跨功能集成场景提前识别
- 风险驱动的测试深度分配

---

## 2. Requirement → Acceptance Scenario Mapping

| Req ID | 需求摘要 | 验收场景 | 必需类别 | 优先级 | 自动化可行性 |
|--------|---------|---------|---------|--------|-------------|
| FR-001 | IM 消息接收与识别 | 需求消息识别/指令消息识别/非文本消息拒绝/接收失败重试 | FUNC,BNDRY,SEC | Critical | Auto |
| FR-002 | 需求结构化与 ID 生成 | ID 生成/空诉求处理/序号满扩展/结构化存储 | FUNC,BNDRY | Critical | Auto |
| FR-003 | 重复提交幂等识别 | 5分钟内重复/超时新需求/不同用户相同文本 | FUNC,BNDRY | High | Auto |
| FR-004a | 状态变更指令解析执行 | 确认指令/驳回指令+意见/权限拒绝/格式错误 | FUNC,BNDRY,SEC | Critical | Auto |
| FR-004b | 查询类指令解析执行 | 进度查询/我的列表/ID不存在/格式错误 | FUNC,BNDRY | High | Auto |
| FR-005 | 评审团多角色独立打分 | 3角色4维度打分/单角色失败重试/全失败通知 | FUNC,PERF | Critical | Auto |
| FR-006 | 评审结论汇总与裁决 | 多数通过/多数反对触发仲裁/1通过1反对1中立 | FUNC,BNDRY | Critical | Auto |
| FR-007 | 人工仲裁处理 | IM推送仲裁/管理员通过/管理员驳回/超时提醒/升级 | FUNC,BNDRY,SEC | Critical | Auto |
| FR-008a | 评审驳回 IM 通知 | 驳回通知含原因/推送失败重试 | FUNC | High | Auto |
| FR-008b | 需求驳回归档 | 状态置已驳回/停止流转/存储失败重试 | FUNC | High | Auto |
| FR-009 | 设计团多角色产出 | 3角色设计/高风险标注/失败重试 | FUNC,PERF | Critical | Auto |
| FR-010 | 设计产出物生成 | 文档+骨架+接口/待确认项标注/存储失败重试 | FUNC | Critical | Auto |
| FR-011 | 设计确认门与 IM 推送 | 推送详情/失败重试/超时提醒/升级 | FUNC,BNDRY | Critical | Auto |
| FR-012 | 设计驳回迭代 | 携带意见迭代/3轮升级/历史保留/空意见拒绝 | FUNC,BNDRY | Critical | Auto |
| FR-013 | 实施团代码生成 | 按设计生成/歧义标注假设/失败重试 | FUNC | Critical | Auto |
| FR-014 | 冲烟验证 | 语法检查/导入检查/启动检查/失败迭代 | FUNC,BNDRY | Critical | Auto |
| FR-015 | 实施结果确认门 | 推送结果/确认落盘/驳回迭代/3轮升级/超时 | FUNC,BNDRY | Critical | Auto |
| FR-016 | Git 提交 | 独立分支/规范Commit/密钥阻止/凭证失效通知 | FUNC,SEC | Critical | Auto |
| FR-017a | 交付档案与总结生成 | 生成档案/存储失败重试 | FUNC | High | Auto |
| FR-017b | 交付完成状态归档 | 状态置已交付/IM通知/通知失败重试 | FUNC | High | Auto |
| FR-018 | 总览看板指标 | 指标卡片展示/空状态引导/未就绪项标注 | FUNC,UI | High | Auto |
| FR-019 | 需求列表与筛选搜索 | 7列表格/筛选/搜索/空结果提示 | FUNC,UI,BNDRY | High | Auto |
| FR-020 | 工作流状态机自动流转 | 自动流转/并发隔离/持久化恢复/非法迁移拒绝 | FUNC,BNDRY | Critical | Auto |
| FR-021 | 看板操作与 IM 同步 | 看板确认/看板驳回/越权拒绝/并发冲突 | FUNC,UI,SEC | High | Auto |
| NFR-001 | IM 消息接收确认时间 p95<5s | Webhook 接收日志统计 | PERF | High | Auto |
| NFR-002 | 单 Agent 执行时间 p95<5min | Agent 执行耗时埋点 | PERF | High | Auto |
| NFR-003 | 看板首屏加载时间 p95<2s | 前端性能埋点（Lighthouse） | PERF | High | Auto |
| NFR-004 | IM 消息推送可靠性 | 至少一次送达，失败重试3次 | FUNC,PERF | High | Auto |
| NFR-005 | 系统可用性 ≥99% | 运行时间/故障时间统计 | PERF | Medium | Manual:external-action |
| NFR-006 | 提交人身份鉴权 | 越权操作100%拒绝 | SEC | Critical | Auto |
| NFR-007 | 操作审计 | 用户操作与Agent执行100%留痕 | SEC | High | Auto |
| NFR-008 | Git 提交禁含密钥 | 含疑似密钥100%阻止 | SEC | Critical | Auto |
| NFR-009 | 并发处理 ≥5并发无串扰 | 并发压力测试 | PERF | High | Auto |
| NFR-010 | 可配置可替换 | IM渠道与LLM供应商可配置 | FUNC | Medium | Auto |
| NFR-011 | 浏览器兼容 Chrome/Edge/Firefox | 跨浏览器兼容测试 | UI | Medium | Manual:visual-judgment |
| IFR-001 | IM 平台双向通信 | Webhook + 事件订阅 | FUNC,SEC | Critical | Auto |
| IFR-002 | Git 仓库操作 | HTTPS/SSH 代码提交 | FUNC | Critical | Auto |
| IFR-003 | 大模型 API 调用 | REST/HTTPS JSON | FUNC | Critical | Auto |
| IFR-005 | MinIO 存储 | S3 API 双向 | FUNC | High | Auto |

---

## 3. Test Category Strategies

### 3.1 FUNC（功能测试）

| 策略 | 说明 |
|------|------|
| **覆盖范围** | 每个 FR 必须覆盖至少 1 个 happy-path + 1 个 error-path 场景 |
| **测试方法** | Given/When/Then 验收标准驱动 |
| **工具** | pytest（后端）、Vitest（前端） |
| **命名规范** | `test_<feature>_<scenario>_<expected>` |
| **数据准备** | fixtures/ 目录提供标准测试数据 |
| **执行频率** | 每次 commit 自动执行 |

### 3.2 BNDRY（边界值测试）

| 策略 | 说明 |
|------|------|
| **覆盖范围** | 每个 FR 的边界条件 + 等价类划分 |
| **重点边界** | ID 格式（REQ-YYYYMMDD-NNN/NNNN）、5分钟幂等窗口、3轮迭代上限、4小时超时、1-5分评分 |
| **测试方法** | 边界值分析（BVA）+ 等价类划分（ECP） |
| **工具** | pytest 参数化 |
| **命名规范** | `test_<feature>_boundary_<boundary_case>` |

### 3.3 SEC（安全测试）

| 策略 | 说明 |
|------|------|
| **覆盖范围** | 输入验证、权限校验、数据泄露防护 |
| **重点场景** | SQL 注入（SQLite）、XSS（React 内置防护）、路径遍历（文件操作）、权限越权（提交人校验） |
| **测试方法** | OWASP Top 10 映射 + 恶意输入注入 |
| **工具** | pytest + 自定义 malicious payload fixtures |
| **命名规范** | `test_<feature>_security_<attack_type>` |

### 3.4 PERF（性能测试）

| 策略 | 说明 |
|------|------|
| **覆盖范围** | NFR-001~003, NFR-005, NFR-009 的阈值验证 |
| **测试方法** | 负载测试 + 基准测试 |
| **工具** | httpx async（API）、Lighthouse（前端） |
| **通过标准** | P95 延迟满足 NFR 阈值 |
| **命名规范** | `test_<feature>_perf_<metric>` |

### 3.5 UI（界面测试）

| 策略 | 说明 |
|------|------|
| **覆盖范围** | FR-018, FR-019, FR-021 的 UI 输出 |
| **测试方法** | Chrome DevTools MCP 交互链：导航 → 交互 → 验证 → 三层检测 |
| **检测层次** | DOM 结构 → 视觉快照 → 控制台日志 |
| **工具** | Playwright + Chrome DevTools MCP |
| **命名规范** | `test_<page>_<interaction>_<expected>` |

---

## 4. NFR Test Method Matrix

| NFR ID | 测试方法 | 工具 | 通过标准 | 负载参数 | 关联 Feature |
|--------|---------|------|---------|---------|-------------|
| NFR-001 | 负载测试 | httpx async + asyncio | P95 < 5s | 100 并发 Webhook 请求, 60s ramp | F003 |
| NFR-002 | 基准测试 | pytest + timeit | P95 < 5min | 单 Agent 执行 10 次取 P95 | F008, F012, F015 |
| NFR-003 | 前端性能 | Lighthouse CI | P95 < 2s (FCP) | 首屏加载 10 次取 P95 | F020, F021 |
| NFR-004 | 可靠性测试 | httpx async + mock | 100% 送达（重试后） | 模拟 IM 推送失败场景 | F011, F015 |
| NFR-005 | 可用性监控 | uptime-kuma / 手动 | ≥99% 运行时间 | 7天连续运行统计 | 全局 |
| NFR-006 | 安全测试 | pytest + malicious fixtures | 100% 越权拒绝 | 模拟越权操作 50 次 | F005, F021 |
| NFR-007 | 审计验证 | pytest + 日志分析 | 100% 留痕 | 检查审计日志完整性 | 全局 |
| NFR-008 | 密钥扫描 | pytest + 正则匹配 | 100% 阻止 | 模拟含密钥代码提交 20 次 | F018 |
| NFR-009 | 并发测试 | asyncio + pytest | 5 并发无状态串扰 | 5 个需求并发执行 | F007, F020 |
| NFR-010 | 配置测试 | pytest + 环境变量 | 切换 IM/LLM 不改代码 | 修改配置验证功能 | 全局 |
| NFR-011 | 兼容性测试 | Playwright + Chrome/Edge/Firefox | 3 浏览器渲染一致 | 最新 2 个大版本 | F020, F021, F022 |

---

## 5. Cross-Feature Integration Scenarios

### 5.1 全流程集成场景

| Scenario ID | 描述 | 涉及 Features | 数据流路径 | 验证点 | ST 阶段 |
|-------------|------|--------------|-----------|--------|---------|
| INT-001 | 需求提交→评审→设计→实施→交付（Happy Path） | F003→F004→F007→F008→F009→F012→F013→F015→F016→F017→F018→F019 | IM→Webhook→结构化→评审→设计→实施→Git→归档 | 状态机完整流转、各阶段产出物正确、最终交付 | System ST |
| INT-002 | 需求提交→评审驳回→归档 | F003→F004→F007→F008→F009→F010→F011 | IM→Webhook→结构化→评审→仲裁→驳回归档 | 驳回通知、状态置已驳回、停止流转 | System ST |
| INT-003 | 需求提交→设计驳回→重新设计→确认→交付 | F003→F004→F007→F012→F013→F014→F015→F016→F017→F018→F019 | IM→结构化→设计→驳回→重新设计→确认→实施→交付 | 版本历史保留、3轮升级、最终交付 | System ST |
| INT-004 | 需求提交→实施驳回→重新实施→确认→交付 | F003→F004→F007→F015→F016→F017→F018→F019→F020 | IM→结构化→实施→冲烟→驳回→重新实施→确认→Git→归档 | 冲烟验证、迭代上限、最终交付 | System ST |
| INT-005 | 看板操作确认→IM 同步 | F020→F021→F022→F023 | 看板→API→状态机→IM通知 | 操作同步、状态一致 | System ST |

### 5.2 基于 §6.2 内部 API 契约的集成场景

| Scenario ID | 契约 ID | 描述 | 数据流路径 | 验证点 |
|-------------|---------|------|-----------|--------|
| INT-006 | C-001 | IM Webhook→消息路由→需求结构化 | Webhook→MessageRouter→RequirementParser→DB | 消息正确解析、需求正确存储 |
| INT-007 | C-002 | 看板指标查询 | API→DashboardService→DB | 指标计算正确 |
| INT-008 | C-003 | 需求列表查询+筛选 | API→DashboardService→DB | 筛选条件正确应用 |
| INT-009 | C-004 | 需求详情查询 | API→DashboardService→DB | 各阶段数据正确聚合 |
| INT-010 | C-005 | 看板确认操作 | API→StateMachine→Huey→Worker | 状态流转正确、IM 同步 |
| INT-011 | C-006 | 看板驳回操作 | API→StateMachine→Huey→Worker | 状态回退、迭代计数 |
| INT-012 | T-001 | IM 消息处理→Huey 任务 | MessageRouter→Huey→Worker | 任务正确入队、Worker 正确执行 |
| INT-013 | T-002 | 评审任务执行 | Huey→ReviewTeam→LLM→DB | 3角色并行打分、结果正确汇总 |
| INT-014 | T-003 | 设计任务执行 | Huey→DesignTeam→LLM→MinIO→DB | 设计文档正确生成、存储 |
| INT-015 | T-004 | 实施任务执行 | Huey→ImplementationTeam→LLM→Git→DB | 代码正确生成、冲烟通过、Git 提交 |
| INT-016 | T-005 | IM 通知发送 | Worker→IM Gateway | 通知正确送达 |
| INT-017 | T-006 | 数据库备份 | Scheduler→SQLite→MinIO | 备份文件正确生成 |

### 5.3 错误场景集成

| Scenario ID | 描述 | 涉及 Features | 错误注入 | 验证点 |
|-------------|------|--------------|---------|--------|
| INT-E001 | LLM API 超时→重试→降级 | F008, F012, F015 | Mock LLM 300s 超时 | 指数退避 3 次、最终通知管理员 |
| INT-E002 | SQLite 写入冲突→WAL 恢复 | F007, F020 | 并发写入同一需求 | 状态一致性、无脏数据 |
| INT-E003 | Git 凭证失效→通知管理员 | F018 | Mock Git push 401 | 代码不丢失、IM 通知 |
| INT-E004 | IM 推送失败→重试 | F011, F015 | Mock IM API 500 | 指数退避 3 次、最终送达 |
| INT-E005 | MinIO 不可用→降级 | F013, F019 | Mock MinIO 连接失败 | 任务暂停、IM 通知 |

---

## 6. Risk-Driven Test Priority

| 风险领域 | 风险等级 | 影响范围 | 测试深度 | 理由 |
|---------|---------|---------|---------|------|
| **IM 权限校验** | 高 | 全系统 | 深度（SEC+FUNC+BNDRY） | 安全边界，越权可导致数据泄露 |
| **状态机流转** | 高 | 全系统 | 深度（FUNC+BNDRY+PERF） | 核心引擎，错误导致流程中断 |
| **LLM Agent 输出质量** | 高 | 评审/设计/实施 | 深度（FUNC+BNDRY） | 输出不可控，需多场景验证 |
| **Git 密钥泄露** | 高 | 代码安全 | 深度（SEC+FUNC） | 安全红线，泄露后果严重 |
| **IM 消息推送可靠性** | 中 | 通知系统 | 标准（FUNC+PERF） | 用户体验，但有重试机制 |
| **SQLite 并发写入** | 中 | 数据层 | 标准（FUNC+BNDRY+PERF） | WAL 模式缓解，但仍需验证 |
| **看板 UI 交互** | 中 | 前端 | 标准（FUNC+UI） | 用户直接接触，但不影响核心流程 |
| **MinIO 存储** | 低 | 文件存储 | 基本（FUNC） | 有重试机制，降级不影响主流程 |
| **配置热替换** | 低 | 运维 | 基本（FUNC） | 非高频操作，手动验证即可 |

---

## 7. Appendix: ATS 摘要

| 维度 | 数量 |
|------|------|
| FR 需求 | 21 |
| NFR 需求 | 11 |
| IFR 需求 | 4 |
| 验收场景 | 68 |
| 跨功能集成场景 | 17 |
| 测试类别 | FUNC, BNDRY, SEC, PERF, UI |
| 高风险领域 | 4（权限、状态机、LLM、密钥） |

---

**Document ends.**
