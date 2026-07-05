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

### Changed
- (none yet)

### Fixed
- (none yet)

---

_Format: [Keep a Changelog](https://keepachangelog.com/) — Updated after every git commit._
