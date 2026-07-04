# DemandFlow 智能需求交付系统 — Design Document

**Date**: 2026-07-04
**Status**: Approved
**SRS Reference**: docs/plans/2026-07-04-demandflow-srs.md
**UCD Reference**: docs/plans/2026-07-04-demandflow-ucd.md

## 1. Architecture

### 1.1 架构方案

**选择**: Approach B — 单体 + 异步 Worker（Monolith + Async Workers）

**核心决策**:
- FastAPI 主进程处理 API/Webhook
- Agent 任务通过 Huey 分发到独立 Worker 进程
- SQLite 作为数据库（WAL 模式）
- LangGraph 实现状态机

### 1.2 逻辑视图（Logical View）

```mermaid
graph TB
    subgraph "Presentation Layer"
        FE[React + Ant Design + AntV G6]
    end
    
    subgraph "API Gateway Layer"
        API[FastAPI Main Process]
        WH[Webhook Handler]
    end
    
    subgraph "Business Logic Layer"
        IM[IM Module]
        REV[Review Module]
        DES[Design Module]
        IMPL[Implementation Module]
        KB[Kanban Module]
        SM[State Machine Module]
    end
    
    subgraph "Agent Execution Layer"
        W1[Worker 1 - Review Agent]
        W2[Worker 2 - Design Agent]
        W3[Worker 3 - Implementation Agent]
    end
    
    subgraph "Data Layer"
        SQLITE[(SQLite File)]
        MINIO[(MinIO)]
        GIT[(Git Repository)]
    end
    
    subgraph "Infrastructure"
        HUEY[Huey Task Queue]
        LLM[LLM APIs]
    end
    
    FE --> API
    WH --> API
    API --> IM
    API --> REV
    API --> DES
    API --> IMPL
    API --> KB
    API --> SM
    IM --> HUEY
    REV --> HUEY
    DES --> HUEY
    IMPL --> HUEY
    HUEY --> W1
    HUEY --> W2
    HUEY --> W3
    W1 --> LLM
    W2 --> LLM
    W3 --> LLM
    W1 --> SQLITE
    W2 --> SQLITE
    W3 --> SQLITE
    W3 --> MINIO
    W3 --> GIT
    KB --> SQLITE
    SM --> SQLITE
```

### 1.3 组件图（Component Diagram）

```mermaid
graph LR
    subgraph "FastAPI Main Process"
        API_CORE[API Core]
        ROUTER[Router Layer]
        SVC[Service Layer]
        REPO[Repository Layer]
        SM_CORE[State Machine Engine]
        EVT[Event Bus]
    end
    
    subgraph "Worker Process"
        TASK_EXEC[Task Executor]
        AGENT_COORD[Agent Coordinator]
        AGENT_POOL[Agent Pool]
    end
    
    subgraph "External"
        IM_SDK[IM Platform SDK]
        LLM_CLIENT[LLM Client]
        GIT_CLIENT[Git Client]
    end
    
    ROUTER --> SVC
    SVC --> REPO
    SVC --> SM_CORE
    SM_CORE --> EVT
    EVT -->|publish| TASK_EXEC
    TASK_EXEC --> AGENT_COORD
    AGENT_COORD --> AGENT_POOL
    AGENT_POOL --> LLM_CLIENT
    TASK_EXEC --> REPO
    API_CORE --> IM_SDK
    AGENT_COORD --> GIT_CLIENT
```

### 1.4 技术栈

| 层 | 技术选型 | 版本 | 理由 |
|---|---------|------|------|
| API | FastAPI | ^0.110 | SRS CON-003 指定，异步支持好 |
| ORM | SQLAlchemy | ^2.0 | FastAPI 生态标准，支持 SQLite |
| 任务队列 | Huey | ^2.5 | 轻量级，SQLite 后端，无额外依赖 |
| 数据库 | SQLite | ^3.45 | 轻量零配置，单文件部署 |
| 状态机 | LangGraph | ^0.2 | SRS CON-002 指定 |
| Agent 框架 | LangChain | ^0.2 | SRS CON-003 指定 |
| 对象存储 | MinIO | latest | SRS CON-003 指定 |
| 前端 | React | ^18 | SRS CON-003 指定 |
| UI 框架 | Ant Design | ^5.x | SRS CON-003 指定 |
| 可视化 | AntV G6 | ^5.x | SRS CON-003 指定 |
| Git 操作 | GitPython | ^3.1 | Python Git 操作标准库 |

### 1.5 NFR 满足策略

| NFR | 策略 |
|-----|------|
| NFR-001 (IM 响应 < 5s) | Webhook Handler 仅做消息验证+入队，返回 202；Huey 异步处理 |
| NFR-002 (Agent < 5min) | Worker 独立进程，LLM 调用超时 300s，Huey 自动重试 |
| NFR-003 (看板首屏 < 2s) | React lazy load + API 分页 |
| NFR-005 (可用性 ≥ 99%) | SQLite WAL 模式 + 文件备份 |
| NFR-009 (并发 5+) | Huey 多 Worker 进程 + SQLite WAL 并发读 |
| NFR-010 (可配置可替换) | SQLAlchemy 抽象层，未来可切换 PostgreSQL |

---

## 2. Key Feature Designs

### 2.1 IM 集成与指令系统（FR-001, FR-002, FR-003, FR-004a, FR-004b）

#### 2.1.1 Overview
处理 IM 消息接收、需求识别、结构化、指令解析，是系统的唯一入口。

#### 2.1.2 Class Diagram

```mermaid
classDiagram
    class IMMessage {
        +str message_id
        +str sender_id
        +str content
        +datetime timestamp
        +MessageType message_type
    }
    
    class MessageType {
        <<enum>>
        REQUIREMENT
        COMMAND
        UNSUPPORTED
    }
    
    class MessageRouter {
        +route(IMMessage) MessageResult
        -identify_type(IMMessage) MessageType
        -extract_command(IMMessage) Command
    }
    
    class RequirementParser {
        +parse(IMMessage) StructuredRequirement
        -extract_intent(str) str
        -extract_constraints(str) list
        -generate_id() str
    }
    
    class IdempotencyChecker {
        +check(int sender_hash, str content) bool
        +store(int sender_hash, str content, str req_id)
    }
    
    class CommandParser {
        +parse(str) Command
        -parse_confirm(str) ConfirmCommand
        -parse_reject(str) RejectCommand
        -parse_progress(str) ProgressCommand
        -parse_list(str) ListCommand
    }
    
    IMMessage --> MessageType
    MessageRouter --> RequirementParser
    MessageRouter --> CommandParser
    MessageRouter --> IdempotencyChecker
```

#### 2.1.3 Sequence Diagram

```mermaid
sequenceDiagram
    participant User as 用户(IM)
    participant WH as Webhook Handler
    participant MR as MessageRouter
    participant ID as IdempotencyChecker
    participant RP as RequirementParser
    participant DB as SQLite
    participant HUEY as Task Queue
    
    User->>WH: 发送消息
    WH->>MR: route(message)
    MR->>MR: identify_type(message)
    
    alt 需求消息
        MR->>ID: check(sender_hash, content)
        alt 重复
            ID-->>MR: True
            MR-->>WH: "需求已存在：REQ-xxx"
        else 新需求
            ID-->>MR: False
            MR->>RP: parse(message)
            RP->>RP: generate_id()
            RP-->>MR: StructuredRequirement
            MR->>DB: save(requirement)
            MR->>ID: store(sender_hash, content, req_id)
            MR->>HUEY: enqueue(review_task, req_id)
            MR-->>WH: "需求已提交：REQ-xxx"
        end
    else 指令消息
        MR->>MR: parse_command(message)
        alt 确认/驳回
            MR->>DB: validate_owner(sender, req_id)
            MR->>HUEY: enqueue(command_task, command)
        else 查询
            MR->>DB: query(sender, query_type)
        end
        MR-->>WH: 指令执行结果
    else 不支持
        MR-->>WH: "本轮仅支持文本需求与指令"
    end
    
    WH-->>User: IM 回复
```

#### 2.1.4 Design Notes

- **需求 ID 格式**: `REQ-YYYYMMDD-NNN`（当日序号，满 999 扩展为 4 位）
- **幂等窗口**: 5 分钟内同提交人相同文本复用 ID
- **指令格式**: "确认 REQ-xxx"、"驳回 REQ-xxx 修改意见XXX"、"进度 REQ-xxx"、"我的列表"
- **权限校验**: 仅提交人可操作自己的需求（FR-004a）

#### 2.1.5 Integration Surface

**Provides**:
| 接口 | 描述 |
|------|------|
| `submit_requirement(IMMessage) -> StructuredRequirement` | 提交需求，触发评审 |
| `execute_command(Command) -> CommandResult` | 执行指令（确认/驳回/查询） |

**Requires**:
| 接口 | 提供者 | 描述 |
|------|--------|------|
| `save_requirement(StructuredRequirement)` | Data Layer | 持久化需求 |
| `validate_owner(str sender, str req_id) -> bool` | Data Layer | 权限校验 |
| `enqueue_review(str req_id)` | State Machine | 触发评审流程 |

---

### 2.2 评审系统（FR-005, FR-006, FR-007, FR-008a, FR-008b）

#### 2.2.1 Overview
多智能体评审团独立打分、汇总裁决、人工仲裁、驳回归档。

#### 2.2.2 Class Diagram

```mermaid
classDiagram
    class ReviewTeam {
        +str requirement_id
        +list~Agent~ agents
        +review(StructuredRequirement) ReviewResult
    }
    
    class ReviewAgent {
        +str role_name
        +score(StructuredRequirement) DimensionScores
        -call_llm(str prompt) str
    }
    
    class DimensionScores {
        +int business_value
        +int technical_feasibility
        +int roi
        +int system_compatibility
        +Verdict verdict
    }
    
    class Verdict {
        <<enum>>
        APPROVE
        REJECT
        NEUTRAL
    }
    
    class ReviewResult {
        +list~DimensionScores~ scores
        +Verdict final_verdict
        +str risk_notes
        +int suggested_priority
    }
    
    class ArbitrationHandler {
        +request_arbitration(str req_id, ReviewResult)
        +handle_response(str req_id, bool approved, str reason)
    }
    
    ReviewTeam --> ReviewAgent
    ReviewAgent --> DimensionScores
    DimensionScores --> Verdict
    ReviewTeam --> ReviewResult
    ArbitrationHandler --> ReviewResult
```

#### 2.2.3 Sequence Diagram

```mermaid
sequenceDiagram
    participant HUEY as Task Queue
    participant RT as ReviewTeam
    participant A1 as 产品分析Agent
    participant A2 as 价值评估Agent
    participant A3 as 技术可行性Agent
    participant DB as SQLite
    participant IM as IM Gateway
    
    HUEY->>RT: review(req_id)
    RT->>A1: score(requirement)
    RT->>A2: score(requirement)
    RT->>A3: score(requirement)
    
    par 并行执行
        A1-->>RT: DimensionScores(通过, 4,5,4,5)
        A2-->>RT: DimensionScores(中立, 3,4,4,3)
        A3-->>RT: DimensionScores(通过, 4,4,5,4)
    end
    
    RT->>RT: aggregate_scores()
    
    alt 多数通过(2+通过)
        RT->>DB: update_status(req_id, 评审通过)
        RT->>HUEY: enqueue(design_task, req_id)
    else 多数反对(2+反对)
        RT->>DB: update_status(req_id, 待仲裁)
        RT->>IM: notify_admin(req_id, review_result)
    else 1通过1反对1中立
        RT->>DB: update_status(req_id, 评审通过)
        RT->>HUEY: enqueue(design_task, req_id)
    end
    
    RT->>DB: save_review_result(req_id, result)
```

#### 2.2.4 Design Notes

- **评审角色**: 产品分析、价值评估、技术可行性（3 角色）
- **评分维度**: 业务价值、技术可行性、投入产出比、系统兼容性（1-5 分）
- **裁决规则**: ≥2 通过自动通过，≥2 反对触发仲裁，1通过1反对1中立视为多数未反对
- **Agent 失败处理**: 指数退避重试 3 次，3 次失败 IM 通知管理员
- **超时**: 仲裁请求 4 小时未回复，累计 3 次升级管理员

#### 2.2.5 Integration Surface

**Provides**:
| 接口 | 描述 |
|------|------|
| `start_review(str req_id) -> ReviewResult` | 触发评审 |
| `handle_arbitration(str req_id, bool approved, str reason)` | 处理仲裁结果 |

**Requires**:
| 接口 | 提供者 | 描述 |
|------|--------|------|
| `call_llm(str prompt) -> str` | Agent Layer | LLM 调用 |
| `update_status(str req_id, Status)` | State Machine | 状态流转 |
| `notify_admin(str req_id, ReviewResult)` | IM Gateway | 通知管理员 |

---

### 2.3 设计系统（FR-009, FR-010, FR-011, FR-012）

#### 2.3.1 Overview
多智能体设计团产出概要设计文档、目录骨架、核心接口定义。

#### 2.3.2 Class Diagram

```mermaid
classDiagram
    class DesignTeam {
        +str requirement_id
        +list~Agent~ agents
        +design(StructuredRequirement, ReviewResult) DesignResult
    }
    
    class DesignAgent {
        +str role_name
        +design(StructuredRequirement) DesignOutput
        -call_llm(str prompt) str
    }
    
    class DesignResult {
        +str document_url
        +list~str~ skeleton_dirs
        +list~Interface~ core_interfaces
        +list~str~ risk_warnings
    }
    
    class Interface {
        +str module_name
        +str method_name
        +str signature
        +bool is_confirmed
    }
    
    class DesignVersionManager {
        +save_version(str req_id, DesignResult)
        +get_versions(str req_id) list~DesignResult~
    }
    
    DesignTeam --> DesignAgent
    DesignTeam --> DesignResult
    DesignResult --> Interface
    DesignVersionManager --> DesignResult
```

#### 2.3.3 Sequence Diagram

```mermaid
sequenceDiagram
    participant HUEY as Task Queue
    participant DT as DesignTeam
    participant A1 as 产品设计Agent
    participant A2 as 技术选型Agent
    participant A3 as 合规风控Agent
    participant DB as SQLite
    participant MINIO as MinIO
    participant IM as IM Gateway
    
    HUEY->>DT: design(req_id)
    DT->>A1: design(requirement)
    DT->>A2: design(requirement)
    DT->>A3: design(requirement)
    
    par 并行执行
        A1-->>DT: DesignOutput(功能边界,用户流程)
        A2-->>DT: DesignOutput(模块划分,技术选型)
        A3-->>DT: DesignOutput(风险评估,合规建议)
    end
    
    DT->>DT: aggregate_design()
    DT->>MINIO: upload(document)
    DT->>DB: save_design_result(req_id, result)
    DT->>DB: update_status(req_id, 设计待确认)
    DT->>IM: notify_submitter(req_id, design_url)
    
    Note over IM: 等待提交人确认/驳回
    
    alt 提交人确认
        IM->>DB: update_status(req_id, 设计确认)
        DB->>HUEY: enqueue(implementation_task, req_id)
    else 提交人驳回+意见
        IM->>DB: update_status(req_id, 设计驳回)
        DB->>HUEY: enqueue(design_task, req_id, feedback)
    end
```

#### 2.3.4 Design Notes

- **设计角色**: 产品设计、技术选型、合规风控（3 角色）
- **产出物**: 概要设计文档 + 代码目录骨架 + 核心接口定义
- **版本管理**: 驳回迭代保留历史版本，3 轮升级管理员
- **超时**: 确认门 4 小时未操作，累计 3 次升级

#### 2.3.5 Integration Surface

**Provides**:
| 接口 | 描述 |
|------|------|
| `start_design(str req_id) -> DesignResult` | 触发设计 |
| `handle_design_feedback(str req_id, str feedback)` | 处理驳回反馈 |

**Requires**:
| 接口 | 提供者 | 描述 |
|------|--------|------|
| `call_llm(str prompt) -> str` | Agent Layer | LLM 调用 |
| `upload_document(bytes, str) -> str` | MinIO | 存储设计文档 |
| `update_status(str req_id, Status)` | State Machine | 状态流转 |
| `notify_submitter(str req_id, str design_url)` | IM Gateway | 通知提交人 |

---

### 2.4 实施系统（FR-013, FR-014, FR-015, FR-016, FR-017a, FR-017b）

#### 2.4.1 Overview
按设计生成源代码、冲烟验证、Git 提交、交付归档。

#### 2.4.2 Class Diagram

```mermaid
classDiagram
    class ImplementationTeam {
        +str requirement_id
        +list~Agent~ agents
        +implement(DesignResult) CodeResult
    }
    
    class CodeGenerator {
        +generate(DesignResult) list~File~
        -call_llm(str prompt) str
    }
    
    class SmokeVerifier {
        +verify(list~File~) VerificationResult
        -check_syntax(list~File~) bool
        -check_imports(list~File~) bool
        -check_startup(list~File~) bool
    }
    
    class VerificationResult {
        +bool syntax_ok
        +bool imports_ok
        +bool startup_ok
        +list~str~ errors
    }
    
    class GitHandler {
        +create_branch(str req_id) str
        +commit(str branch, list~File~ files, str message) str
        +push(str branch)
    }
    
    class ArchiveManager {
        +create_archive(str req_id, DesignResult, CodeResult, str commit_id) Archive
    }
    
    ImplementationTeam --> CodeGenerator
    ImplementationTeam --> SmokeVerifier
    SmokeVerifier --> VerificationResult
    ImplementationTeam --> GitHandler
    ImplementationTeam --> ArchiveManager
```

#### 2.4.3 Sequence Diagram

```mermaid
sequenceDiagram
    participant HUEY as Task Queue
    participant IT as ImplementationTeam
    participant CG as CodeGenerator
    participant SV as SmokeVerifier
    participant GH as GitHandler
    participant DB as SQLite
    participant MINIO as MinIO
    participant IM as IM Gateway
    
    HUEY->>IT: implement(req_id)
    IT->>CG: generate(design)
    CG-->>IT: list~File~
    
    IT->>SV: verify(files)
    SV->>SV: check_syntax()
    SV->>SV: check_imports()
    SV->>SV: check_startup()
    SV-->>IT: VerificationResult
    
    alt 验证失败
        IT->>DB: update_status(req_id, 实施中)
        IT->>HUEY: enqueue(implementation_task, req_id)
    else 验证通过
        IT->>DB: update_status(req_id, 实施待验收)
        IT->>IM: notify_submitter(req_id, verification_result)
        
        Note over IM: 等待提交人确认/驳回
        
        alt 提交人确认
            IT->>GH: create_branch(req_id)
            GH-->>IT: branch_name
            IT->>GH: commit(branch, files, message)
            GH-->>IT: commit_id
            IT->>GH: push(branch)
            
            IT->>MINIO: upload(archive)
            IT->>DB: save_archive(req_id, archive)
            IT->>DB: update_status(req_id, 已交付)
            IT->>IM: notify_delivered(req_id, commit_id)
        else 提交人驳回+意见
            IT->>DB: update_status(req_id, 实施中)
            IT->>HUEY: enqueue(implementation_task, req_id, feedback)
        end
    end
```

#### 2.4.4 Design Notes

- **冲烟验证**: 语法/编译检查 + 导入检查 + 启动检查
- **密钥检测**: 提交前扫描 API Key/密码/Token 模式，阻止提交
- **Git 规范**: 独立分支 `feature/REQ-xxx`，Conventional Commits 格式
- **交付档案**: 各阶段产出物引用 + 交付总结

#### 2.4.5 Integration Surface

**Provides**:
| 接口 | 描述 |
|------|------|
| `start_implementation(str req_id) -> CodeResult` | 触发实施 |
| `handle_impl_feedback(str req_id, str feedback)` | 处理驳回反馈 |

**Requires**:
| 接口 | 提供者 | 描述 |
|------|--------|------|
| `call_llm(str prompt) -> str` | Agent Layer | LLM 调用 |
| `git_commit(str branch, list files) -> str` | Git Client | Git 操作 |
| `upload_archive(bytes, str) -> str` | MinIO | 存储交付档案 |
| `update_status(str req_id, Status)` | State Machine | 状态流转 |
| `notify_submitter(str req_id, CodeResult)` | IM Gateway | 通知提交人 |

---

### 2.5 看板仪表盘（FR-018, FR-019, FR-021）

#### 2.5.1 Overview
总览指标、需求列表筛选搜索、看板操作与 IM 同步。

#### 2.5.2 Class Diagram

```mermaid
classDiagram
    class DashboardService {
        +get_metrics() DashboardMetrics
        +get_requirements(filters) list~Requirement~
        +get_requirement_detail(str req_id) RequirementDetail
    }
    
    class DashboardMetrics {
        +int total_count
        +float approval_rate
        +int in_progress_count
    }
    
    class RequirementListRequest {
        +str status_filter
        +str stage_filter
        +str submitter_filter
        +str search_keyword
        +int page
        +int page_size
    }
    
    class RequirementDetail {
        +StructuredRequirement requirement
        +ReviewResult review_result
        +DesignResult design_result
        +CodeResult code_result
        +list~StatusTransition~ timeline
    }
    
    class StatusTransition {
        +Status from_status
        +Status to_status
        +datetime timestamp
        +str trigger
    }
    
    class DashboardAPI {
        +GET /api/dashboard/metrics
        +GET /api/requirements
        +GET /api/requirements/{id}
        +POST /api/requirements/{id}/confirm
        +POST /api/requirements/{id}/reject
    }
    
    DashboardService --> DashboardMetrics
    DashboardService --> RequirementListRequest
    DashboardService --> RequirementDetail
    RequirementDetail --> StatusTransition
    DashboardAPI --> DashboardService
```

#### 2.5.3 API 设计

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | `/api/dashboard/metrics` | 获取总览指标 |
| GET | `/api/requirements?page=1&page_size=10&status=&stage=&submitter=&search=` | 需求列表 |
| GET | `/api/requirements/{req_id}` | 需求详情 |
| POST | `/api/requirements/{req_id}/confirm` | 确认操作 |
| POST | `/api/requirements/{req_id}/reject` | 驳回操作（body: {reason}） |

#### 2.5.4 Design Notes

- **实时同步**: 看板操作通过 WebSocket 推送更新
- **筛选**: URL query params 持久化，支持分享
- **分页**: 默认 10 条/页，支持 10/20/50

#### 2.5.5 Integration Surface

**Provides**:
| 接口 | 描述 |
|------|------|
| `GET /api/dashboard/metrics` | 总览指标 |
| `GET /api/requirements` | 需求列表 |
| `POST /api/requirements/{id}/confirm` | 确认操作 |

**Requires**:
| 接口 | 提供者 | 描述 |
|------|--------|------|
| `query_requirements(filters) -> list` | Data Layer | 查询需求 |
| `update_status(str req_id, Status)` | State Machine | 状态流转 |
| `notify_submitter(str req_id, str action)` | IM Gateway | 同步 IM |

---

### 2.6 状态机引擎（FR-020）

#### 2.6.1 Overview
需求全生命周期状态流转，基于 LangGraph 实现，支持自动流转、并发隔离、持久化恢复。

#### 2.6.2 Class Diagram

```mermaid
classDiagram
    class StateMachine {
        +str requirement_id
        +Status current_status
        +transition(Event) Status
        +can_transition(Event) bool
    }
    
    class Status {
        <<enum>>
        PENDING_REVIEW
        REVIEW_APPROVED
        PENDING_ARBITRATION
        REJECTED
        IN_DESIGN
        DESIGN_PENDING_CONFIRM
        DESIGN_CONFIRMED
        DESIGN_REJECTED
        IN_IMPLEMENTATION
        IMPL_PENDING_ACCEPTANCE
        IMPL_APPROVED
        IMPL_REJECTED
        DELIVERED
        TERMINATED
    }
    
    class Event {
        <<enum>>
        SUBMIT
        REVIEW_PASS
        REVIEW_REJECT
        ARBITRATION_APPROVE
        ARBITRATION_REJECT
        DESIGN_CONFIRM
        DESIGN_REJECT
        IMPL_CONFIRM
        IMPL_REJECT
        TIMEOUT
    }
    
    class StateTransitionTable {
        +dict~Status, dict~Event, Status~~ transitions
        +get_next(Status, Event) Status
    }
    
    class PersistenceManager {
        +save_state(str req_id, Status)
        +load_state(str req_id) Status
    }
    
    StateMachine --> Status
    StateMachine --> Event
    StateMachine --> StateTransitionTable
    StateMachine --> PersistenceManager
```

#### 2.6.3 状态流转图

```mermaid
stateDiagram-v2
    [*] --> 待评审: 提交需求
    待评审 --> 评审通过: 多数通过
    待评审 --> 待仲裁: 多数反对
    待评审 --> 已驳回: 仲裁驳回
    
    待仲裁 --> 评审通过: 管理员通过
    待仲裁 --> 已驳回: 管理员驳回
    待仲裁 --> 待仲裁: 超时提醒(3次升级)
    
    评审通过 --> 设计中: 自动流转
    设计中 --> 设计待确认: 设计完成
    设计待确认 --> 设计确认: 提交人确认
    设计待确认 --> 设计驳回: 提交人驳回
    设计驳回 --> 设计中: 重新设计(≤3轮)
    设计驳回 --> 待处理: 超过3轮
    
    设计确认 --> 实施中: 自动流转
    实施中 --> 实施待验收: 冲烟通过
    实施中 --> 实施中: 冲烟失败(≤3轮)
    实施待验收 --> 验收通过: 提交人确认
    实施待验收 --> 验收驳回: 提交人驳回
    验收驳回 --> 实施中: 重新实施(≤3轮)
    验收驳回 --> 待处理: 超过3轮
    
    验收通过 --> 已交付: Git提交+归档
    已交付 --> [*]
    已驳回 --> [*]
    待处理 --> [*]
```

#### 2.6.4 Design Notes

- **状态持久化**: 每次流转写入 SQLite，系统重启从最后状态恢复
- **并发隔离**: 多需求状态独立，互不影响
- **非法迁移拒绝**: 状态机拒绝不合法的状态转换请求
- **超时提醒**: 决策门 4 小时未操作，累计 3 次升级管理员

#### 2.6.5 Integration Surface

**Provides**:
| 接口 | 描述 |
|------|------|
| `transition(str req_id, Event) -> Status` | 执行状态流转 |
| `get_status(str req_id) -> Status` | 获取当前状态 |
| `can_transition(str req_id, Event) -> bool` | 检查是否可流转 |

**Requires**:
| 接口 | 提供者 | 描述 |
|------|--------|------|
| `save_state(str req_id, Status)` | Data Layer | 持久化状态 |
| `load_state(str req_id) -> Status` | Data Layer | 加载状态 |

---

## 3. Data Model

### 3.1 ER Diagram

```mermaid
erDiagram
    REQUIREMENTS {
        text id PK "REQ-YYYYMMDD-NNN"
        text original_text "原始需求文本"
        text summary "核心诉求摘要"
        text submitter_id "提交人ID"
        text submitter_name "提交人姓名"
        text tags "功能标签JSON"
        text estimated_scope "预估范围"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
        text current_stage "当前阶段"
        text current_status "当前状态"
    }
    
    REVIEW_RESULTS {
        integer id PK "自增主键"
        text requirement_id FK "关联需求ID"
        text agent_role "评审角色"
        integer business_value "业务价值1-5"
        integer technical_feasibility "技术可行性1-5"
        integer roi "投入产出比1-5"
        integer system_compatibility "系统兼容性1-5"
        text verdict "通过/反对/中立"
        text comments "评语"
        datetime scored_at "评分时间"
    }
    
    DESIGN_RESULTS {
        integer id PK "自增主键"
        text requirement_id FK "关联需求ID"
        text agent_role "设计角色"
        text document_url "设计文档URL"
        text skeleton_dirs "目录骨架JSON"
        text core_interfaces "核心接口JSON"
        text risk_warnings "风险提示JSON"
        datetime created_at "创建时间"
        integer version "版本号"
    }
    
    IMPLEMENTATION_RESULTS {
        integer id PK "自增主键"
        text requirement_id FK "关联需求ID"
        text code_files "代码文件列表JSON"
        text verification_result "冲烟验证结果JSON"
        text branch_name "Git分支名"
        text commit_id "Git Commit ID"
        text commit_message "Commit信息"
        datetime committed_at "提交时间"
    }
    
    DELIVERY_ARCHIVES {
        integer id PK "自增主键"
        text requirement_id FK "关联需求ID"
        text review_ref "评审产出物引用"
        text design_ref "设计产出物引用"
        text implementation_ref "实施产出物引用"
        text summary "交付总结"
        datetime delivered_at "交付时间"
    }
    
    STATUS_HISTORY {
        integer id PK "自增主键"
        text requirement_id FK "关联需求ID"
        text from_status "原状态"
        text to_status "新状态"
        text trigger_event "触发事件"
        text trigger_user "触发用户"
        datetime triggered_at "触发时间"
    }
    
    ARBITRATION_REQUESTS {
        integer id PK "自增主键"
        text requirement_id FK "关联需求ID"
        text admin_id "管理员ID"
        text review_summary "评审摘要"
        text admin_response "管理员回复"
        datetime requested_at "请求时间"
        datetime responded_at "回复时间"
        integer timeout_count "超时提醒次数"
    }
    
    IDEMPOTENCY_STORE {
        integer id PK "自增主键"
        integer sender_hash "发送人哈希"
        text content_hash "内容哈希"
        text requirement_id "关联需求ID"
        datetime created_at "创建时间"
    }
    
    REQUIREMENTS ||--o{ REVIEW_RESULTS : "has reviews"
    REQUIREMENTS ||--o{ DESIGN_RESULTS : "has designs"
    REQUIREMENTS ||--o{ IMPLEMENTATION_RESULTS : "has implementations"
    REQUIREMENTS ||--o{ DELIVERY_ARCHIVES : "has archive"
    REQUIREMENTS ||--o{ STATUS_HISTORY : "has history"
    REQUIREMENTS ||--o{ ARBITRATION_REQUESTS : "has arbitration"
```

### 3.2 存储策略

| 表 | 预估行数(1年) | 索引策略 |
|---|--------------|---------|
| requirements | 10,000 | PK(id), IX(submitter_id), IX(current_stage, current_status) |
| review_results | 30,000 | IX(requirement_id), IX(agent_role) |
| design_results | 20,000 | IX(requirement_id), IX(version) |
| implementation_results | 15,000 | IX(requirement_id) |
| delivery_archives | 10,000 | IX(requirement_id) |
| status_history | 50,000 | IX(requirement_id), IX(triggered_at) |
| arbitration_requests | 1,000 | IX(requirement_id) |
| idempotency_store | 50,000 | IX(sender_hash, content_hash), TTL 5分钟过期清理 |

---

## 4. API / Interface Design

### 4.1 外部接口

| ID | 外部系统 | 方向 | 协议 | 数据格式 |
|----|---------|------|------|---------|
| IFR-001 | IM 平台（单渠道） | 双向 | Webhook + 事件订阅 | JSON |
| IFR-002 | Git 仓库 | 出站 | Git HTTPS/SSH | 代码 + Commit |
| IFR-003 | 大模型 API | 出站 | REST/HTTPS | JSON |
| IFR-005 | MinIO | 双向 | S3 API | 代码包/设计文档 |

### 4.2 内部 API 契约

| Method | Endpoint | Request | Response | Contract ID |
|--------|----------|---------|----------|-------------|
| POST | `/webhook/im/{platform}` | IM Webhook Payload | `{status, message}` | C-001 |
| GET | `/api/dashboard/metrics` | - | `DashboardMetrics` | C-002 |
| GET | `/api/requirements` | QueryParams | `PaginatedList<Requirement>` | C-003 |
| GET | `/api/requirements/{req_id}` | Path: req_id | `RequirementDetail` | C-004 |
| POST | `/api/requirements/{req_id}/confirm` | Path: req_id | `{status, message}` | C-005 |
| POST | `/api/requirements/{req_id}/reject` | Path: req_id, Body: `{reason}` | `{status, message}` | C-006 |

### 4.3 任务队列契约

| Task Name | Parameters | Return | Contract ID |
|-----------|-----------|--------|-------------|
| `process_im_message` | `message_id, sender_id, content` | `StructuredRequirement` | T-001 |
| `run_review` | `requirement_id` | `ReviewResult` | T-002 |
| `run_design` | `requirement_id` | `DesignResult` | T-003 |
| `run_implementation` | `requirement_id` | `CodeResult` | T-004 |
| `send_im_notification` | `recipient_id, message_type, content` | `bool` | T-005 |
| `backup_database` | - | `str` | T-006 |

---

## 5. UI/UX Design

### 5.1 前端架构

| 层 | 技术选型 | 版本 | 理由 |
|---|---------|------|------|
| 框架 | React | ^18 | SRS CON-003 指定 |
| 构建工具 | Vite | ^5.x | 快速开发体验 |
| UI 组件库 | Ant Design | ^5.x | SRS CON-003 + UCD 已定义 |
| 路由 | React Router | ^6.x | SPA 标准路由 |
| 状态管理 | Zustand | ^4.x | 轻量级 |
| 数据请求 | SWR | ^2.x | 缓存、重新验证 |
| 可视化 | AntV G6 | ^5.x | 状态机可视化 |

### 5.2 UCD 组件 → 实现映射

| UCD 组件 | 实现组件 | 文件路径 |
|----------|---------|---------|
| 顶部导航栏 | `Header` | `src/components/layout/Header.tsx` |
| 指标卡片 | `MetricCard` | `src/components/dashboard/MetricCard.tsx` |
| 筛选栏 | `FilterBar` | `src/components/requirements/FilterBar.tsx` |
| 数据表格 | `RequirementTable` | `src/components/requirements/RequirementTable.tsx` |
| 状态标签 | `StatusTag` | `src/components/common/StatusTag.tsx` |
| 操作确认弹窗 | `ActionModal` | `src/components/common/ActionModal.tsx` |
| 消息提示 | `message` (Ant Design) | 直接使用 |
| 空状态 | `EmptyState` | `src/components/common/EmptyState.tsx` |

### 5.3 路由设计

| Path | Component | 描述 |
|------|-----------|------|
| `/` | `DashboardPage` | 看板首页 |
| `/requirements` | `RequirementListPage` | 需求列表 |
| `/requirements/:id` | `RequirementDetailPage` | 需求详情 |

---

## 6. Third-Party Dependencies

### 6.1 Python 后端

| 库 | 版本 | 许可证 | 用途 |
|---|------|--------|------|
| fastapi | ^0.110 | MIT | Web API 框架 |
| uvicorn | ^0.27 | BSD | ASGI 服务器 |
| sqlalchemy | ^2.0 | MIT | ORM |
| alembic | ^1.13 | MIT | 数据库迁移 |
| huey | ^2.5 | MIT | 轻量级任务队列 |
| langchain | ^0.2 | MIT | Agent 框架 |
| langgraph | ^0.2 | MIT | 状态机引擎 |
| langchain-openai | ^0.1 | MIT | OpenAI 集成 |
| gitpython | ^3.1 | BSD | Git 操作 |
| minio | ^7.2 | Apache 2.0 | MinIO 客户端 |
| pydantic | ^2.6 | MIT | 数据验证 |
| httpx | ^0.27 | BSD | HTTP 客户端 |
| python-dotenv | ^1.0 | BSD | 环境变量 |
| cryptography | ^42.0 | Apache 2.0 | HMAC 签名验证 |

### 6.2 前端

| 库 | 版本 | 许可证 | 用途 |
|---|------|--------|------|
| react | ^18.3 | MIT | UI 框架 |
| react-dom | ^18.3 | MIT | React DOM 渲染 |
| react-router-dom | ^6.22 | MIT | 路由 |
| antd | ^5.15 | MIT | UI 组件库 |
| @ant-design/icons | ^5.3 | MIT | 图标 |
| @ant-design/g6 | ^5.x | MIT | 图可视化 |
| zustand | ^4.5 | MIT | 状态管理 |
| swr | ^2.2 | MIT | 数据请求 |
| dayjs | ^1.11 | MIT | 日期处理 |

### 6.3 依赖兼容性

| 组合 | 兼容性 | 备注 |
|------|--------|------|
| Python 3.10+ | ✓ | LangChain/LangGraph 最低要求 |
| FastAPI + SQLAlchemy 2.0 | ✓ | 官方推荐组合 |
| LangChain + LangGraph | ✓ | 同一生态 |
| React 18 + Ant Design 5 | ✓ | 官方支持 |
| Vite 5 + React 18 | ✓ | @vitejs/plugin-react 官方支持 |

---

## 7. Testing Strategy

### 7.1 测试哲学

- **TDD + 质量门禁**: Red → Green → Refactor → Coverage → Mutation
- **测试金字塔**: 单元测试 > 集成测试 > E2E 测试

### 7.2 工具选型

| 层 | 工具 | 版本 | 用途 |
|---|------|------|------|
| Python 测试 | pytest | ^8.0 | 测试框架 |
| Python 覆盖 | pytest-cov | ^4.1 | 覆盖率统计 |
| Python 变异 | mutmut | ^2.4 | 变异测试 |
| Mock | pytest-mock | ^3.12 | Mock 工具 |
| API 测试 | httpx | ^0.27 | FastAPI TestClient |
| 前端测试 | Vitest | ^1.6 | 前端单元测试 |
| 前端覆盖 | @vitest/coverage-v8 | ^1.6 | 前端覆盖率 |
| E2E 测试 | Playwright | ^1.42 | 浏览器自动化 |
| Lint | ESLint + Prettier | latest | 前端代码规范 |
| Lint | Ruff | ^0.4 | Python 代码规范 |

### 7.3 覆盖率门禁

| 指标 | 阈值 | 工具 |
|------|------|------|
| 行覆盖率 (Line) | >= 80% | pytest-cov / Vitest |
| 分支覆盖率 (Branch) | >= 70% | pytest-cov / Vitest |
| 变异得分 (Mutation) | >= 75% | mutmut |

---

## 8. Deployment / Infrastructure

### 8.1 部署架构

```mermaid
graph TB
    subgraph "单机部署"
        subgraph "Python 进程"
            API[FastAPI Main Process<br/>:8000]
            W1[Huey Worker 1]
            W2[Huey Worker 2]
        end
        
        subgraph "Node 进程"
            FE[React Dev Server<br/>:5173 或 Nginx :80]
        end
        
        subgraph "数据文件"
            SQLITE[(SQLite<br/>data/demandflow.db)]
            HUEY_DB[(SQLite<br/>data/huey_queue.db)]
            MINIO_DIR[(MinIO<br/>data/minio/)]
        end
    end
    
    subgraph "外部服务"
        LLM[LLM APIs]
        GIT[Git Repository]
    end
    
    API --> SQLITE
    API --> HUEY_DB
    W1 --> SQLITE
    W2 --> SQLITE
    W1 --> MINIO_DIR
    W2 --> MINIO_DIR
    W1 --> LLM
    W2 --> LLM
    W1 --> GIT
    W2 --> GIT
    FE --> API
```

### 8.2 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | SQLite 文件路径 | `sqlite:///data/demandflow.db` |
| `HUEY_URL` | Huey 队列路径 | `sqlite:///data/huey_queue.db` |
| `LLM_API_KEY` | LLM API 密钥 | - |
| `LLM_MODEL` | LLM 模型名 | `gpt-4` |
| `GIT_REPO_URL` | Git 仓库地址 | - |
| `GIT_BRANCH_PREFIX` | 分支前缀 | `feature/` |
| `MINIO_ENDPOINT` | MinIO 地址 | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO 访问密钥 | - |
| `MINIO_SECRET_KEY` | MinIO 密钥 | - |
| `IM_PLATFORM` | IM 平台类型 | `dingtalk` |
| `IM_WEBHOOK_SECRET` | Webhook 签名密钥 | - |
| `DEBUG` | 调试模式 | `false` |

---

## 9. Development Plan

### 9.1 里程碑

| 里程碑 | 范围 | 退出标准 |
|--------|------|----------|
| **M1: Foundation** | 项目骨架、CI、核心抽象 | 项目可运行、测试可执行、CI 通过 |
| **M2: IM Integration** | IM 接入、指令系统、需求结构化 | 可通过 IM 提交需求并获取 ID |
| **M3: Review System** | 多智能体评审、仲裁、驳回 | 评审流程自动完成，仲裁可处理 |
| **M4: Design System** | 多智能体设计、确认门、迭代 | 设计产出物可生成，确认/驳回可操作 |
| **M5: Implementation** | 代码生成、冲烟验证、Git 提交 | 代码可生成并提交到 Git |
| **M6: Kanban Dashboard** | 看板首页、列表、详情、筛选 | 看板可查看所有需求状态 |
| **M7: Polish & Release** | NFR 验证、文档、示例 | 全部测试通过，NFR 达标 |

### 9.2 Feature 分解

| Feature ID | 名称 | Priority | Mapped FRs | 依赖 |
|------------|------|----------|------------|------|
| F001 | 项目骨架与基础设施 | P0 | - | - |
| F002 | 数据模型与迁移 | P0 | - | F001 |
| F003 | IM Webhook 接入 | P0 | FR-001 | F002 |
| F004 | 需求结构化与 ID 生成 | P0 | FR-002, FR-003 | F003 |
| F005 | 状态变更指令系统 | P0 | FR-004a | F004 |
| F006 | 查询指令系统 | P0 | FR-004b | F004 |
| F007 | 状态机引擎 | P0 | FR-020 | F002 |
| F008 | 评审团多角色打分 | P0 | FR-005 | F007 |
| F009 | 评审结论汇总与裁决 | P0 | FR-006 | F008 |
| F010 | 人工仲裁处理 | P0 | FR-007 | F009 |
| F011 | 评审驳回通知与归档 | P0 | FR-008a, FR-008b | F010 |
| F012 | 设计团多角色产出 | P0 | FR-009 | F007 |
| F013 | 设计产出物生成 | P0 | FR-010 | F012 |
| F014 | 设计确认门与迭代 | P0 | FR-011, FR-012 | F013 |
| F015 | 实施团代码生成 | P0 | FR-013 | F007 |
| F016 | 冲烟验证 | P0 | FR-014 | F015 |
| F017 | 实施确认门 | P0 | FR-015 | F016 |
| F018 | Git 提交与密钥检测 | P0 | FR-016 | F017 |
| F019 | 交付档案与状态归档 | P0 | FR-017a, FR-017b | F018 |
| F020 | 看板首页指标 | P1 | FR-018 | F002 |
| F021 | 需求列表与筛选搜索 | P1 | FR-019 | F002 |
| F022 | 需求详情页 | P1 | - | F020, F021 |
| F023 | 看板操作与 IM 同步 | P1 | FR-021 | F022 |

### 9.3 依赖链（Critical Path）

```mermaid
graph LR
    F001[F001: 项目骨架] --> F002[F002: 数据模型]
    F002 --> F003[F003: IM接入]
    F003 --> F004[F004: 需求结构化]
    F004 --> F005[F005: 状态指令]
    F004 --> F006[F006: 查询指令]
    F002 --> F007[F007: 状态机]
    F007 --> F008[F008: 评审打分]
    F008 --> F009[F009: 评审裁决]
    F009 --> F010[F010: 人工仲裁]
    F010 --> F011[F011: 驳回归档]
    F007 --> F012[F012: 设计产出]
    F012 --> F013[F013: 设计产出物]
    F013 --> F014[F014: 设计确认门]
    F007 --> F015[F015: 代码生成]
    F015 --> F016[F016: 冲烟验证]
    F016 --> F017[F017: 实施确认门]
    F017 --> F018[F018: Git提交]
    F018 --> F019[F019: 交付归档]
    F002 --> F020[F020: 看板指标]
    F002 --> F021[F021: 需求列表]
    F020 --> F022[F022: 详情页]
    F021 --> F022
    F022 --> F023[F023: 看板同步]
```

**关键路径**: F001 → F002 → F003 → F004 → F007 → F008 → F009 → F010 → F011

### 9.4 Milestone 计划

| Milestone | Features | 预估时间 |
|-----------|----------|----------|
| M1: Foundation | F001, F002 | 2 天 |
| M2: IM Integration | F003, F004, F005, F006 | 3 天 |
| M3: Review System | F007, F008, F009, F010, F011 | 4 天 |
| M4: Design System | F012, F013, F014 | 3 天 |
| M5: Implementation | F015, F016, F017, F018, F019 | 4 天 |
| M6: Kanban Dashboard | F020, F021, F022, F023 | 3 天 |
| M7: Polish & Release | NFR 验证、文档、示例 | 2 天 |
| **总计** | 23 Features | **21 天** |

### 9.5 风险登记

| 风险 | 影响 | 概率 | 缓解策略 |
|------|------|------|----------|
| LLM API 响应超时 | Agent 执行失败 | 中 | 指数退避 3 次 + 超时 300s |
| LLM 输出质量不稳定 | 评审/设计结果不可用 | 高 | Prompt 调优 + 人工仲裁兜底 |
| SQLite 并发写入瓶颈 | 状态流转失败 | 低 | WAL 模式 + 短事务 |
| Git 凭证失效 | 代码落盘失败 | 低 | 凭证检查 + IM 通知管理员 |
| IM 平台 API 变更 | 消息收发失败 | 低 | 抽象适配层 + 配置化 |

---

## 10. Additional Notes

### 10.1 未来迁移路径

**SQLite → PostgreSQL**: 当并发用户 > 50 或需求条目 > 10,000 时
**Huey → Celery**: 当需要分布式任务队列或 Redis/RabbitMQ 时

迁移方式：SQLAlchemy 支持多数据库，Huey 可切换 backend。

### 10.2 备份策略

```bash
# SQLite 热备份
sqlite3 data/demandflow.db ".backup data/backups/demandflow_$(date +%Y%m%d_%H%M%S).db"

# 定时任务（Huey scheduled task）
@huey.schedule(crontab(minute=0, hour=2))  # 每天凌晨2点
def backup_database():
    # 执行备份并上传到 MinIO
    pass
```

---

**Document ends.**
