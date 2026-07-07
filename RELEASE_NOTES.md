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

### Changed
- (none yet)

### Fixed
- (none yet)

---

_Format: [Keep a Changelog](https://keepachangelog.com/) — Updated after every git commit._
