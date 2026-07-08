# Release Notes — demandflow

## [Unreleased]

### Added
- Initial project scaffold
- SRS document (docs/plans/2026-07-04-demandflow-srs.md)
- UCD style guide (docs/plans/2026-07-04-demandflow-ucd.md)
- Design document (docs/plans/2026-07-04-demandflow-design.md)
- Acceptance Test Strategy (docs/plans/2026-07-04-demandflow-ats.md)
- F001 项目骨架与基础设施 — FastAPI 应用工厂 (create_app)、SQLite+WAL 数据库连接 (get_db)、Huey SQLite 任务队列 (init_huey)、pydantic-settings 配置管理 (get_settings)；12 tests，覆盖率 97% line / 83% branch / 93% mutation；11 ISO 29119 验收用例全部通过
- F002 数据模型与迁移 — 8 SQLAlchemy 模型 (Requirements, ReviewResults, DesignResults, ImplementationResults, DeliveryArchives, StatusHistory, ArbitrationRequests, IdempotencyStore)、CHECK 约束 (id GLOB, ratings 1-5, verdict IN, timeout_count>=0)、JSON 字段、复合索引、Alembic 初始迁移；29 tests，覆盖率 98% line / 98% branch；28 ISO 29119 验收用例全部通过
- F003 IM Webhook 接入 — WebhookHandler 接收 IM 消息、MessageRouter 路由消息到对应处理器、POST /webhook/im/{platform} 端点；12 tests，覆盖率 96% line / 96% branch；12 ISO 29119 验收用例全部通过
- F004 需求结构化与 ID 生成 — RequirementParser 解析需求消息生成结构化数据、IdempotencyChecker 防重复提交、REQ-YYYYMMDD-NNN 格式 ID；27 tests，覆盖率 97% line / 97% branch；13 ISO 29119 验收用例全部通过
- F005 状态变更指令系统 — CommandParser 解析确认/驳回指令、PermissionChecker 校验提交人权限、CommandExecutor 执行指令并记录状态历史；31 tests，覆盖率 97% line / 97% branch；15 ISO 29119 验收用例全部通过
- F006 查询指令系统 — CommandParser 扩展支持进度/我的列表查询、QueryExecutor 执行查询返回格式化结果、ProgressCommand/ListCommand 数据类；15 tests，覆盖率 97% line / 97% branch；15 ISO 29119 验收用例全部通过
- F007 状态机引擎 — StateMachine 需求全生命周期状态流转、StateTransitionTable 合法迁移表、PersistenceManager SQLite 持久化、Status/Event 枚举；23 tests，覆盖率 98% line / 98% branch；18 ISO 29119 验收用例全部通过
- F008 评审团多角色打分 — ReviewTeam 多角色并行打分、ReviewAgent 4维度评分、Verdict 裁决枚举、指数退避重试、全失败通知；15 tests，覆盖率 96% line / ~93% branch
- F009 评审结论汇总与裁决 — AggregationService 汇总 3 角色结论、ArbitrationHandler 仲裁生命周期管理、_decide 裁决规则（≥2通过自动通过，≥2反对触发仲裁）；18 tests，覆盖率 98% line / 98% branch
- F010 人工仲裁处理 — ArbitrationNotifier IM 推送仲裁请求（指数退避重试 3 次）、ArbitrationTimeoutMonitor 4 小时超时检测与 3 次升级、CommandExecutor 仲裁指令路由；14 tests，覆盖率 98% line / 100% branch
- F011 评审驳回通知与归档 — RejectionNotifier 驳回通知（指数退避重试 3 次）、format_rejection_message 格式化中文消息、复用 F010 NotificationFailedError；10 tests，覆盖率 97% line / 100% branch
- F012 设计团多角色产出 — DesignTeam 协调 3 角色（产品设计、技术选型、合规风控）DesignAgent 并行产出概要设计、指数退避重试、全失败通知、高风险 [高风险] 标注；19 tests，覆盖率 95% line / 90% branch
- F013 设计产出物生成 — DesignOutputHandler 生成结构化设计文档（JSON）、代码目录骨架、核心接口验证标记、待确认项标注、MinIO 上传（3 次指数退避重试）、状态流转（IN_DESIGN→DESIGN_PENDING_CONFIRM）、提交人 IM 通知；17 tests，覆盖率 100% line（design_output_handler.py）
- F014 设计确认门与迭代 — DesignConfirmationHandler 确认/驳回处理、ConfirmationTimeoutMonitor 4h 超时检测与升级、3 轮驳回迭代上限（MAX_RETRY → TERMINATED）、EmptyRejectReasonError 空驳回原因校验、状态流转（DESIGN_CONFIRMED→IN_IMPLEMENTATION, DESIGN_REJECTED→IN_DESIGN）；24 tests，覆盖率 87% line（design_confirmation_handler.py）
- F015 实施团代码生成 — ImplementationTeam 3 角色并行代码生成（后端开发/前端开发/质量保障）、ImplementationAgent + retry_with_backoff（复用 F008）、CodeOutput/CodeResult 聚合与去重、歧义标注假设（ambiguity_notes）、ImplementationResults 持久化；17 tests，覆盖率 91% line（implementation_team.py）
- F016 冲烟验证 — SmokeVerifier 语法检查（ast.parse）、导入验证（importlib）、启动验证（exec）、VerificationResult 聚合；17 tests，覆盖率 96% line / 96% branch
- F017 实施确认门 — ImplementationConfirmationHandler 确认/驳回处理（3次重试上限）、ConfirmationTimeoutMonitor 4h 超时检测与升级、状态流转（IMPL_APPROVED→DELIVERED, IMPL_REJECTED→IN_IMPLEMENTATION）、EMPTY_REJECT_REASON_ERROR；18 tests，覆盖率 95% line / ~82% branch
- F018 Git 提交与密钥检测 — SecretDetector 8 模式密钥扫描（AWS/GitHub/Bearer/PEM）、GitHandler 分支创建/提交/推送、GitCommitOrchestrator 全流程编排（扫描→分支→提交→推送+3次重试）、push_enabled 开关、CredentialExpiredError 认证错误分离；21 tests，覆盖率 94% line（git_handler.py）/ 100% branch / 总覆盖 95.06%
- F019 交付档案与状态归档 — DeliveryArchiveHandler 全流程（档案JSON生成→MinIO上传3次退避重试→DB持久化→状态机IMPL_APPROVED→DELIVERED→IM通知3次退避重试）、TypeError 非重试异常直接传播、Upload失败通知管理员不影响已提交Git代码、NotificationFailedError 通知耗尽异常；19 tests，覆盖率 100% line（delivery_archive_handler.py）/ 总覆盖 95.15%
- F020 看板首页指标 — DashboardService.get_metrics() 3 指标（总需求数/评审通过率/进行中数）、GET /api/dashboard/metrics 端点；前端 Vite + React 19 + Ant Design v6，MetricCard（加载骨架屏/错误徽章）、DashboardPage（EmptyState/自动刷新）；18 tests（10 后端 + 8 前端），覆盖率 95% 总覆盖
- F021 需求列表与筛选搜索 — RequirementsService.get_requirements() 分页筛选搜索、GET /api/requirements 端点；前端 RequirementsListPage（Ant Design Table + Select + Search + Pagination）、React Router 路由；18 tests（13 后端 + 5 前端）

### Changed
- (none yet)

### Fixed
- (none yet)

---

_Format: [Keep a Changelog](https://keepachangelog.com/) — Updated after every git commit._
