# DemandFlow 延迟需求 Backlog

**Date**: 2026-07-04
**Status**: Deferred — for future SRS increment pickup
**Source**: 2026-07-04-demandflow-srs.md（最小闭环范围之外的已规划未来能力）

本文件保留本轮 SRS 显式延后的需求条目（EARS + 验收标准），供后续 `increment-request.json` 触发的增量需求轮次拾取。每条均映射至用户既定路线图阶段（阶段2：多智能体团队化 / 阶段3：生产级增强）。

> 注：多智能体团队架构、LangGraph、技术栈等为**既定硬约束（CON-001~003）**，不属于延迟项——本轮已纳入。

---

## DF-001: 详细架构与技术设计阶段 [阶段2]
**Priority**: Should
**EARS**: When 概要设计经提交人确认，the system shall 触发详细架构团（系统架构/数据设计/接口设计 3 角色）输出落地级技术设计（系统架构图、数据模型、完整接口契约、数据库表结构）。
**Acceptance Criteria**:
- Given 概要设计确认，when 触发详细架构，then 3 角色产出系统架构图（Mermaid）+ 数据模型 + 接口契约 + 表结构
- Given 提交人确认详细设计，when 处理，then 进入代码实施
- Given 提交人驳回 + 意见，when 处理，then 携带意见重新设计（3 轮上限）

## DF-002: 完整自动测试套件与代码审计 [阶段3]
**Priority**: Should
**EARS**: When 源代码生成完成，the system shall 触发测试用例 Agent 生成单元测试与集成测试用例、代码审计 Agent 检查规范/安全/性能隐患，并自动执行输出测试报告。
**Acceptance Criteria**:
- Given 代码生成完成，when 触发，then 生成单元测试 + 集成测试用例并自动执行
- Given 代码审计识别问题，when 处理，then 输出审计报告并标记修复项
- Given 测试未通过，when 处理，then 自动迭代修复（计入 3 轮上限）

## DF-003: 多 IM 渠道接入 [阶段3]
**Priority**: Should
**EARS**: When 管理员配置新的 IM 渠道（企业微信/飞书/钉钉/Slack），the system shall 通过统一消息网关接入并屏蔽各平台差异。
**Acceptance Criteria**:
- Given 配置新 IM 渠道，when 接入，then 通过统一网关收发消息且业务无感
- Given 多渠道用户，when 交互，then 渠道差异被屏蔽，指令与推送行为一致

## DF-004: 详情页时间轴/版本对比/执行日志 [阶段2]
**Priority**: Should
**EARS**: When 用户访问需求详情页，the system shall 展示全流程节点时间轴、各版次产出物卡片、版本差异对比与执行日志。
**Acceptance Criteria**:
- Given 访问详情页，when 加载，then 展示从提交到当前的节点时间轴
- Given 多版次设计/代码，when 操作，then 支持版本差异对比
- Given 查看执行日志，when 操作，then 展示各阶段 Agent 执行过程与中间结果

## DF-005: 历史方案复用与语义需求去重 [阶段3]
**Priority**: Could
**EARS**: When 新需求入库，the system shall 基于向量知识库（Chroma）检索历史相似方案与代码，并语义识别重复需求。
**Acceptance Criteria**:
- Given 新需求入库，when 检索，then 返回相似历史方案与可复用代码并标注相似度
- Given 语义相似需求，when 识别，then 提示提交人可能重复并引用历史需求
- Given 用户选择复用，when 处理，then 引用历史方案加速交付

## DF-006: IM 追加补充/优先级设置指令 [阶段3]
**Priority**: Could
**EARS**: When 提交人发送"追加 REQ-xxx 补充内容"或"优先级 REQ-xxx 高/中/低"，the system shall 解析并更新需求。
**Acceptance Criteria**:
- Given "追加 REQ-xxx 补充内容"，when 解析，then 追加补充内容到需求并重新触发受影响阶段
- Given "优先级 REQ-xxx 高"，when 解析，then 更新需求优先级
- Given 需求已进入实施后追加，when 处理，then 提示影响范围并确认

## DF-007: 看板漏斗图/实时动态流/平均时长指标 [阶段3]
**Priority**: Could
**EARS**: When 用户访问总览看板，the system shall 展示阶段漏斗图、实时动态流与平均设计/交付时长指标。
**Acceptance Criteria**:
- Given 访问总览看板，when 加载，then 展示阶段漏斗图（各阶段数量与转化率）
- Given 有新动态，when 加载，then 滚动展示最新提交需求与最新完成节点
- Given 指标就绪，when 加载，then 展示平均设计时长与平均交付时长

## DF-008: 富媒体消息处理（图片/文件/语音）[阶段3]
**Priority**: Could
**EARS**: When 用户在 IM 发送图片/文件/语音消息，the system shall 识别并解析为需求或附件。
**Acceptance Criteria**:
- Given 发送图片/截图，when 识别，then OCR 或视觉解析为需求文本
- Given 发送文件，when 识别，then 作为需求附件关联
- Given 发送语音，when 识别，then 转写为需求文本

## DF-009: 超时阈值可配置 [阶段3]
**Priority**: Could
**EARS**: When 管理员配置节点超时阈值，the system shall 按配置阈值触发超时提醒（替代固定 4 小时）。
**Acceptance Criteria**:
- Given 管理员设置超时阈值，when 配置，then 各决策门按新阈值触发提醒
- Given 未配置，when 处理，then 默认 4 小时
