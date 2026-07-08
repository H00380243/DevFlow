"""Seed test data for DemandFlow demo."""
from datetime import datetime, timezone, timedelta
from app.models import (
    Requirements, ReviewResults, DesignResults, ImplementationResults,
    DeliveryArchives, StatusHistory, ArbitrationRequests, init_db, Base,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///data/demandflow.db")
init_db(engine)

now = datetime.now(timezone.utc)

with Session(engine) as session:
    # === REQ-001: 已完成交付 ===
    r1 = Requirements(
        id="REQ-20260708-001",
        original_text="用户登录模块需要支持手机号+验证码登录，以及微信扫码登录",
        summary="用户登录模块 — 手机号验证码 + 微信扫码登录",
        submitter_id="user_zhang",
        submitter_name="张明",
        tags=["登录", "认证", "高优先级"],
        estimated_scope="2人周",
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(hours=1),
        current_stage="delivery",
        current_status="DELIVERED",
    )
    session.add(r1)
    session.flush()

    session.add_all([
        ReviewResults(
            requirement_id=r1.id, agent_role="产品分析",
            business_value=5, technical_feasibility=4, roi=4, system_compatibility=5,
            verdict="通过", comments="登录模块是刚需，方案成熟", scored_at=now - timedelta(days=4, hours=20),
        ),
        ReviewResults(
            requirement_id=r1.id, agent_role="价值评估",
            business_value=5, technical_feasibility=5, roi=3, system_compatibility=4,
            verdict="通过", comments="业务价值高，建议加快排期", scored_at=now - timedelta(days=4, hours=19),
        ),
        ReviewResults(
            requirement_id=r1.id, agent_role="技术可行性",
            business_value=4, technical_feasibility=5, roi=4, system_compatibility=5,
            verdict="通过", comments="验证码 + 微信登录技术方案成熟，无风险", scored_at=now - timedelta(days=4, hours=18),
        ),
    ])
    session.add(DesignResults(
        requirement_id=r1.id, agent_role="产品设计",
        document_url="http://localhost:9000/designs/req001-v1.pdf",
        skeleton_dirs=["app/auth/", "app/auth/providers/", "tests/auth/"],
        core_interfaces=["POST /api/auth/send-code", "POST /api/auth/login-by-phone", "POST /api/auth/login-by-wechat"],
        risk_warnings=["短信通道故障影响验证码登录"],
        created_at=now - timedelta(days=3), version=1,
    ))
    session.add(DesignResults(
        requirement_id=r1.id, agent_role="技术选型",
        document_url="http://localhost:9000/designs/req001-tech-v1.pdf",
        skeleton_dirs=["app/auth/wechat/", "app/auth/sms/"],
        core_interfaces=["WeChatAuthProvider", "SmsCodeProvider"],
        risk_warnings=[],
        created_at=now - timedelta(days=3), version=1,
    ))
    session.add(ImplementationResults(
        requirement_id=r1.id,
        code_files=[
            {"path": "app/auth/router.py", "lines": 45},
            {"path": "app/auth/providers/sms.py", "lines": 28},
            {"path": "app/auth/providers/wechat.py", "lines": 36},
        ],
        verification_result={"syntax": "pass", "imports": "pass", "startup": "pass"},
        branch_name="feature/req001-login", commit_id="a1b2c3d4e5",
        commit_message="feat: implement phone+wechat login",
        committed_at=now - timedelta(days=1, hours=12),
    ))
    session.add(DeliveryArchives(
        requirement_id=r1.id,
        review_ref="REVIEW-001", design_ref="DESIGN-001",
        implementation_ref="IMPL-001",
        summary="""
### 交付内容
- 手机号验证码登录接口
- 微信扫码登录接口
- 登录状态管理（JWT）
### 交付物
- 后端代码 3 个模块
- 接口文档
- 单元测试覆盖
""",
        delivered_at=now - timedelta(hours=2),
    ))
    session.add(StatusHistory(requirement_id=r1.id, from_status=None, to_status="PENDING_REVIEW", trigger_event="REQUIREMENT_SUBMITTED", trigger_user="user_zhang", triggered_at=now - timedelta(days=5)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="PENDING_REVIEW", to_status="IN_REVIEW", trigger_event="REVIEW_STARTED", trigger_user="system", triggered_at=now - timedelta(days=4, hours=21)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="IN_REVIEW", to_status="REVIEW_PASSED", trigger_event="REVIEW_COMPLETED", trigger_user="system", triggered_at=now - timedelta(days=4, hours=18)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="REVIEW_PASSED", to_status="IN_DESIGN", trigger_event="DESIGN_STARTED", trigger_user="system", triggered_at=now - timedelta(days=3, hours=12)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="IN_DESIGN", to_status="DESIGN_PENDING_CONFIRM", trigger_event="DESIGN_COMPLETED", trigger_user="system", triggered_at=now - timedelta(days=3)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="DESIGN_PENDING_CONFIRM", to_status="DESIGN_CONFIRMED", trigger_event="CONFIRM", trigger_user="user_zhang", triggered_at=now - timedelta(days=2, hours=20)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="DESIGN_CONFIRMED", to_status="IN_IMPLEMENTATION", trigger_event="IMPLEMENTATION_STARTED", trigger_user="system", triggered_at=now - timedelta(days=2, hours=18)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="IN_IMPLEMENTATION", to_status="IMPL_PENDING_ACCEPTANCE", trigger_event="IMPLEMENTATION_COMPLETED", trigger_user="system", triggered_at=now - timedelta(days=1, hours=14)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="IMPL_PENDING_ACCEPTANCE", to_status="IMPL_APPROVED", trigger_event="CONFIRM", trigger_user="user_zhang", triggered_at=now - timedelta(days=1, hours=6)))
    session.add(StatusHistory(requirement_id=r1.id, from_status="IMPL_APPROVED", to_status="DELIVERED", trigger_event="DELIVERY_COMPLETED", trigger_user="system", triggered_at=now - timedelta(hours=2)))

    # === REQ-002: 评审中 ===
    r2 = Requirements(
        id="REQ-20260709-002",
        original_text="数据看板需要支持按日期范围筛选，以及导出为 Excel 文件",
        summary="数据看板 — 日期筛选 + Excel 导出",
        submitter_id="user_li",
        submitter_name="李华",
        tags=["看板", "导出", "中优先级"],
        estimated_scope="1人周",
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=2),
        current_stage="review",
        current_status="IN_REVIEW",
    )
    session.add(r2)
    session.flush()

    session.add_all([
        ReviewResults(
            requirement_id=r2.id, agent_role="产品分析",
            business_value=4, technical_feasibility=5, roi=3, system_compatibility=4,
            verdict="通过", comments="导出功能是常见需求，方案清晰", scored_at=now - timedelta(hours=3),
        ),
        ReviewResults(
            requirement_id=r2.id, agent_role="价值评估",
            business_value=3, technical_feasibility=4, roi=2, system_compatibility=4,
            verdict="通过", comments="中等价值，建议迭代二期再做", scored_at=now - timedelta(hours=2),
        ),
    ])
    session.add(StatusHistory(requirement_id=r2.id, from_status=None, to_status="PENDING_REVIEW", trigger_event="REQUIREMENT_SUBMITTED", trigger_user="user_li", triggered_at=now - timedelta(hours=6)))
    session.add(StatusHistory(requirement_id=r2.id, from_status="PENDING_REVIEW", to_status="IN_REVIEW", trigger_event="REVIEW_STARTED", trigger_user="system", triggered_at=now - timedelta(hours=4)))

    # === REQ-003: 设计待确认 ===
    r3 = Requirements(
        id="REQ-20260709-003",
        original_text="审批流程引擎支持自定义审批链，包括会签、或签、条件分支",
        summary="审批流程引擎 — 自定义审批链（会签/或签/条件分支）",
        submitter_id="user_wang",
        submitter_name="王芳",
        tags=["流程引擎", "审批", "高优先级", "核心模块"],
        estimated_scope="3人周",
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(hours=3),
        current_stage="design",
        current_status="DESIGN_PENDING_CONFIRM",
    )
    session.add(r3)
    session.flush()

    session.add_all([
        ReviewResults(
            requirement_id=r3.id, agent_role="产品分析",
            business_value=5, technical_feasibility=3, roi=4, system_compatibility=4,
            verdict="通过", comments="审批引擎是平台化能力，需关注复杂度", scored_at=now - timedelta(days=2, hours=12),
        ),
        ReviewResults(
            requirement_id=r3.id, agent_role="价值评估",
            business_value=5, technical_feasibility=4, roi=3, system_compatibility=3,
            verdict="通过", comments="高价值，但实施周期长", scored_at=now - timedelta(days=2, hours=11),
        ),
        ReviewResults(
            requirement_id=r3.id, agent_role="技术可行性",
            business_value=4, technical_feasibility=3, roi=3, system_compatibility=3,
            verdict="反对", comments="自定义审批链复杂度高，建议分阶段实施", scored_at=now - timedelta(days=2, hours=10),
        ),
    ])
    session.add(DesignResults(
        requirement_id=r3.id, agent_role="产品设计",
        document_url="http://localhost:9000/designs/req003-v1.pdf",
        skeleton_dirs=["app/engine/", "app/engine/nodes/", "app/engine/routes/"],
        core_interfaces=["POST /api/engine/chain", "POST /api/engine/chain/:id/execute"],
        risk_warnings=["[高风险] 条件分支节点复杂度高，需结合实际业务流程验证"],
        created_at=now - timedelta(hours=5), version=1,
    ))
    session.add(DesignResults(
        requirement_id=r3.id, agent_role="技术选型",
        document_url="http://localhost:9000/designs/req003-tech-v1.pdf",
        skeleton_dirs=["app/engine/dsl/", "app/engine/executor/"],
        core_interfaces=["ChainDSLParser", "WorkflowExecutor"],
        risk_warnings=["[高风险] 嵌套条件分支的性能优化需要进一步调研"],
        created_at=now - timedelta(hours=5), version=1,
    ))
    session.add(StatusHistory(requirement_id=r3.id, from_status=None, to_status="PENDING_REVIEW", trigger_event="REQUIREMENT_SUBMITTED", trigger_user="user_wang", triggered_at=now - timedelta(days=3)))
    session.add(StatusHistory(requirement_id=r3.id, from_status="PENDING_REVIEW", to_status="IN_REVIEW", trigger_event="REVIEW_STARTED", trigger_user="system", triggered_at=now - timedelta(days=2, hours=16)))
    session.add(StatusHistory(requirement_id=r3.id, from_status="IN_REVIEW", to_status="REVIEW_PASSED", trigger_event="REVIEW_COMPLETED", trigger_user="system", triggered_at=now - timedelta(days=2, hours=10)))
    session.add(StatusHistory(requirement_id=r3.id, from_status="REVIEW_PASSED", to_status="IN_DESIGN", trigger_event="DESIGN_STARTED", trigger_user="system", triggered_at=now - timedelta(days=1, hours=8)))
    session.add(StatusHistory(requirement_id=r3.id, from_status="IN_DESIGN", to_status="DESIGN_PENDING_CONFIRM", trigger_event="DESIGN_COMPLETED", trigger_user="system", triggered_at=now - timedelta(hours=5)))

    # === REQ-004: 待评审（新建） ===
    r4 = Requirements(
        id="REQ-20260709-004",
        original_text="系统通知模块需要支持站内信、邮件、企业微信三种渠道推送",
        summary="通知模块 — 站内信 + 邮件 + 企业微信推送",
        submitter_id="user_zhang",
        submitter_name="张明",
        tags=["通知", "多渠道", "中优先级"],
        estimated_scope="2人周",
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(minutes=30),
        current_stage="review",
        current_status="PENDING_REVIEW",
    )
    session.add(r4)
    session.flush()
    session.add(StatusHistory(requirement_id=r4.id, from_status=None, to_status="PENDING_REVIEW", trigger_event="REQUIREMENT_SUBMITTED", trigger_user="user_zhang", triggered_at=now - timedelta(hours=1)))

    # === REQ-005: 已驳回（归档） ===
    r5 = Requirements(
        id="REQ-20260707-005",
        original_text="实现区块链存证功能，将关键审批数据上链",
        summary="区块链存证 — 审批数据上链",
        submitter_id="user_li",
        submitter_name="李华",
        tags=["区块链", "实验性"],
        estimated_scope="5人周",
        created_at=now - timedelta(days=4),
        updated_at=now - timedelta(days=2),
        current_stage="review",
        current_status="TERMINATED",
    )
    session.add(r5)
    session.flush()

    session.add_all([
        ReviewResults(
            requirement_id=r5.id, agent_role="产品分析",
            business_value=2, technical_feasibility=2, roi=1, system_compatibility=1,
            verdict="反对", comments="当前阶段无需区块链存证", scored_at=now - timedelta(days=3),
        ),
        ReviewResults(
            requirement_id=r5.id, agent_role="价值评估",
            business_value=1, technical_feasibility=2, roi=1, system_compatibility=1,
            verdict="反对", comments="投入产出比过低，建议暂缓", scored_at=now - timedelta(days=3),
        ),
        ReviewResults(
            requirement_id=r5.id, agent_role="技术可行性",
            business_value=2, technical_feasibility=3, roi=1, system_compatibility=2,
            verdict="反对", comments="技术上可行但业务场景不明确", scored_at=now - timedelta(days=3),
        ),
    ])
    session.add(StatusHistory(requirement_id=r5.id, from_status=None, to_status="PENDING_REVIEW", trigger_event="REQUIREMENT_SUBMITTED", trigger_user="user_li", triggered_at=now - timedelta(days=4)))
    session.add(StatusHistory(requirement_id=r5.id, from_status="PENDING_REVIEW", to_status="IN_REVIEW", trigger_event="REVIEW_STARTED", trigger_user="system", triggered_at=now - timedelta(days=3, hours=12)))
    session.add(StatusHistory(requirement_id=r5.id, from_status="IN_REVIEW", to_status="TERMINATED", trigger_event="REVIEW_REJECTED", trigger_user="system", triggered_at=now - timedelta(days=3)))

    # === REQ-006: 实施待确认 ===
    r6 = Requirements(
        id="REQ-20260708-006",
        original_text="日志系统需要支持按照服务名、级别、关键字搜索，以及日志归档策略",
        summary="日志系统 — 搜索 + 归档策略",
        submitter_id="user_wang",
        submitter_name="王芳",
        tags=["日志", "运维", "高优先级"],
        estimated_scope="2人周",
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(hours=4),
        current_stage="implementation",
        current_status="IMPL_PENDING_ACCEPTANCE",
    )
    session.add(r6)
    session.flush()

    session.add_all([
        ReviewResults(
            requirement_id=r6.id, agent_role="产品分析",
            business_value=4, technical_feasibility=4, roi=4, system_compatibility=5,
            verdict="通过", comments="日志集中管理是基础设施需求", scored_at=now - timedelta(days=5),
        ),
        ReviewResults(
            requirement_id=r6.id, agent_role="价值评估",
            business_value=4, technical_feasibility=5, roi=3, system_compatibility=4,
            verdict="通过", comments="长期价值高", scored_at=now - timedelta(days=5),
        ),
        ReviewResults(
            requirement_id=r6.id, agent_role="技术可行性",
            business_value=4, technical_feasibility=4, roi=4, system_compatibility=4,
            verdict="通过", comments="采用 ELK 方案成熟", scored_at=now - timedelta(days=5),
        ),
    ])
    session.add(DesignResults(
        requirement_id=r6.id, agent_role="产品设计",
        document_url="http://localhost:9000/designs/req006-v1.pdf",
        skeleton_dirs=["app/logging/", "app/logging/search/", "app/logging/archive/"],
        core_interfaces=["GET /api/logs/search", "POST /api/logs/archive/policy"],
        risk_warnings=[],
        created_at=now - timedelta(days=3), version=1,
    ))
    session.add(ImplementationResults(
        requirement_id=r6.id,
        code_files=[
            {"path": "app/logging/service.py", "lines": 62},
            {"path": "app/logging/search/elastic.py", "lines": 45},
            {"path": "app/logging/archive/scheduler.py", "lines": 38},
        ],
        verification_result={"syntax": "pass", "imports": "pass", "startup": "pass"},
        branch_name="feature/req006-logging", commit_id="f6e7d8c9b0",
        commit_message="feat: implement log search and archive",
        committed_at=now - timedelta(hours=8),
    ))
    session.add(StatusHistory(requirement_id=r6.id, from_status=None, to_status="PENDING_REVIEW", trigger_event="REQUIREMENT_SUBMITTED", trigger_user="user_wang", triggered_at=now - timedelta(days=6)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="PENDING_REVIEW", to_status="IN_REVIEW", trigger_event="REVIEW_STARTED", trigger_user="system", triggered_at=now - timedelta(days=5, hours=12)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="IN_REVIEW", to_status="REVIEW_PASSED", trigger_event="REVIEW_COMPLETED", trigger_user="system", triggered_at=now - timedelta(days=5, hours=6)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="REVIEW_PASSED", to_status="IN_DESIGN", trigger_event="DESIGN_STARTED", trigger_user="system", triggered_at=now - timedelta(days=4, hours=12)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="IN_DESIGN", to_status="DESIGN_PENDING_CONFIRM", trigger_event="DESIGN_COMPLETED", trigger_user="system", triggered_at=now - timedelta(days=3, hours=18)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="DESIGN_PENDING_CONFIRM", to_status="DESIGN_CONFIRMED", trigger_event="CONFIRM", trigger_user="user_wang", triggered_at=now - timedelta(days=3, hours=6)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="DESIGN_CONFIRMED", to_status="IN_IMPLEMENTATION", trigger_event="IMPLEMENTATION_STARTED", trigger_user="system", triggered_at=now - timedelta(days=2, hours=12)))
    session.add(StatusHistory(requirement_id=r6.id, from_status="IN_IMPLEMENTATION", to_status="IMPL_PENDING_ACCEPTANCE", trigger_event="IMPLEMENTATION_COMPLETED", trigger_user="system", triggered_at=now - timedelta(hours=10)))

    session.commit()

print("Seeded 6 requirements with full lifecycle data.")
print()
print("Summary:")
print(f"  REQ-001 (DELIVERED)        — complete flow, all artifacts")
print(f"  REQ-002 (IN_REVIEW)        — 2/3 reviews done, awaiting 3rd")
print(f"  REQ-003 (DESIGN_PENDING)   — design done, awaiting submitter confirm")
print(f"  REQ-004 (PENDING_REVIEW)   — newly submitted, no reviews yet")
print(f"  REQ-005 (TERMINATED)       — rejected by all 3 reviewers")
print(f"  REQ-006 (IMPL_PENDING)     — implementation done, awaiting confirm")
