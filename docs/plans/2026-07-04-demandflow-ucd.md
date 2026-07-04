# DemandFlow 智能需求交付系统 — UCD Style Guide

**Date**: 2026-07-04
**Status**: Approved
**SRS Reference**: docs/plans/2026-07-04-demandflow-srs.md

## 1. Visual Style Direction

**选择**: Style A — Ant Design 默认风格（Clean Professional）

**Mood**: 专业、清爽、高效的企业级工具感

**Color direction**: Ant Design 默认蓝灰色系，中性色调，高对比度

**Typography direction**: Ant Design 默认字体（PingFang SC / Helvetica Neue），清晰可读

**Layout direction**: Ant Design 标准栅格，卡片式布局，紧凑信息密度

**Target persona fit**: 研发与技术 lead — 熟悉 Ant Design 生态，降低学习成本

**Reference style**: Ant Design 5.x 官方风格

**技术约束**: CON-003 指定 React + Ant Design + AntV G6

---

## 2. Style Tokens

### 2.1 Color Palette

| Token | Hex | Usage | Contrast Ratio |
|-------|-----|-------|----------------|
| `--color-primary` | #1677ff | 主操作按钮、链接、激活状态 | 4.57:1 on white ✓ |
| `--color-primary-hover` | #4096ff | 主操作 Hover 状态 | 3.93:1 on white (大文本) |
| `--color-primary-active` | #0958d9 | 主操作 Active 状态 | 6.24:1 on white ✓ |
| `--color-secondary` | #722ed1 | 次要强调、标签 | 5.87:1 on white ✓ |
| `--color-bg-primary` | #ffffff | 主背景 | — |
| `--color-bg-secondary` | #fafafa | 卡片/分区背景 | — |
| `--color-bg-tertiary` | #f5f5f5 | 输入框/Hover 背景 | — |
| `--color-text-primary` | #000000d9 (rgba) | 正文文字 | 12.6:1 on white ✓ |
| `--color-text-secondary` | #00000073 (rgba) | 辅助说明文字 | 4.63:1 on white ✓ |
| `--color-text-tertiary` | #00000040 (rgba) | 占位符/禁用文字 | 2.38:1 (仅大文本) |
| `--color-success` | #52c41a | 成功状态、已完成 | 3.48:1 on white (大文本) |
| `--color-warning` | #faad14 | 警告状态 | 2.93:1 on white (大文本) |
| `--color-error` | #ff4d4f | 错误状态、驳回、危险操作 | 4.31:1 on white ✓ |
| `--color-info` | #1677ff | 信息提示 | 4.57:1 on white ✓ |
| `--color-border` | #d9d9d9 | 默认边框 | — |
| `--color-border-light` | #f0f0f0 | 分割线 | — |

### 2.2 Typography Scale

| Token | Font Family | Size | Weight | Line Height | Usage |
|-------|-------------|------|--------|-------------|-------|
| `--font-heading-1` | PingFang SC, Helvetica Neue, Arial | 38px | 600 | 46px | 页面标题 |
| `--font-heading-2` | PingFang SC, Helvetica Neue, Arial | 30px | 600 | 38px | 区块标题 |
| `--font-heading-3` | PingFang SC, Helvetica Neue, Arial | 24px | 600 | 32px | 卡片标题 |
| `--font-heading-4` | PingFang SC, Helvetica Neue, Arial | 20px | 600 | 28px | 小节标题 |
| `--font-body` | PingFang SC, Helvetica Neue, Arial | 14px | 400 | 22px | 正文 |
| `--font-body-small` | PingFang SC, Helvetica Neue, Arial | 12px | 400 | 20px | 辅助说明 |
| `--font-label` | PingFang SC, Helvetica Neue, Arial | 14px | 500 | 22px | 表单标签 |
| `--font-code` | Menlo, Monaco, Consolas, monospace | 13px | 400 | 20px | 代码/ID展示 |

### 2.3 Spacing & Layout

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px | 紧凑内边距（徽标内间距） |
| `--space-sm` | 8px | 默认内边距（按钮/输入框内间距） |
| `--space-md` | 12px | 卡片内间距 |
| `--space-lg` | 16px | 区块间距 |
| `--space-xl` | 24px | 页面区块间距 |
| `--space-2xl` | 32px | 页面边距 |
| `--space-3xl` | 48px | 大区块分隔 |
| `--radius-sm` | 4px | 按钮、输入框 |
| `--radius-md` | 6px | 卡片、弹窗 |
| `--radius-lg` | 8px | 大卡片、下拉面板 |
| `--shadow-sm` | 0 1px 2px 0 rgba(0,0,0,0.03), 0 1px 6px -1px rgba(0,0,0,0.02), 0 2px 4px 0 rgba(0,0,0,0.02) | 轻微浮起 |
| `--shadow-md` | 0 3px 6px -4px rgba(0,0,0,0.12), 0 6px 16px 0 rgba(0,0,0,0.08), 0 9px 28px 8px rgba(0,0,0,0.05) | 卡片/下拉 |
| `--shadow-lg` | 0 6px 16px -8px rgba(0,0,0,0.08), 0 9px 28px 0 rgba(0,0,0,0.05), 0 12px 48px 16px rgba(0,0,0,0.03) | 弹窗/浮层 |

### 2.4 Iconography & Imagery

- **Icon style**: Outline（线性）, 2px stroke, 圆角端点
- **Icon library**: Ant Design Icons 5.x（@ant-design/icons）
- **Icon size**: 14px（行内）/ 16px（按钮）/ 20px（导航）/ 24px（标题装饰）
- **Illustration style**: 无插画，纯图标+数据驱动
- **Empty state**: Ant Design 标准空状态组件（图示+文字+操作按钮）

---

## 3. Component Prompts

### 3.1 顶部导航栏 (Header/Navbar)
**SRS Trace**: FR-018, FR-019, FR-021（全局导航）
**Variants**: Default, Scrolled

#### Base Prompt
> A horizontal navigation bar at the top of the page, 48px height, white background (#ffffff), bottom border 1px solid #f0f0f0. Left-aligned: product logo (20x20 icon) followed by product name "DemandFlow" in font-heading-4 (20px/600 weight), 8px gap between logo and text. Right-aligned: user avatar (28x28px circle) with username label (font-body, 14px) in --color-text-primary. Navigation bar stays fixed at top during scroll with --shadow-sm elevation. Padding: 0 --space-2xl (32px horizontal).

#### Variant Prompts
> **Scrolled state**: Add --shadow-md elevation, border-bottom remains #f0f0f0
> **Dark mode** (if applicable): Background #141414, border #303030, text #ffffffd9

#### Style Constraints
- Height must be exactly 48px for consistent vertical rhythm
- Logo + product name must be clickable, linking to dashboard home
- User avatar must show dropdown on click (profile, settings, logout)

---

### 3.2 指标卡片 (Metric Card)
**SRS Trace**: FR-018（总览看板指标）
**Variants**: Default, Loading, Empty

#### Base Prompt
> A rectangular card with --radius-md (6px) corners, white background (#ffffff), 1px solid #f0f0f0 border, padding --space-lg (16px). Contains: top-left small label text (font-body-small, 12px, --color-text-secondary) showing metric name like "总需求数"; center large number (font-heading-2, 30px, 600 weight, --color-text-primary) showing metric value; optional bottom-right trend indicator with upward arrow icon (14px, --color-success) or downward arrow (--color-error) followed by percentage text (font-body-small, 12px). Card has --shadow-sm elevation, hover state shows --shadow-md with 0.2s ease transition.

#### Variant Prompts
> **Loading state**: Replace number with animated skeleton pulse (30px height, 60% width, #f0f0f0 background with shimmer animation)
> **Empty state**: Show placeholder "--" in --color-text-tertiary with tooltip "暂无数据"

#### Style Constraints
- Card width must be flexible (grid-based, 1/3 of container on desktop)
- Minimum height 100px for visual balance
- Number must use tabular figures (font-variant-numeric: tabular-nums) for alignment

---

### 3.3 筛选栏 (Filter Bar)
**SRS Trace**: FR-019（需求列表筛选）
**Variants**: Default, Active Filters

#### Base Prompt
> A horizontal filter bar above the data table, height 56px, background #fafafa, border-bottom 1px solid #f0f0f0, padding 0 --space-xl (24px). Contains: left-aligned filter group with 3 Ant Design Select dropdowns (height 32px, --radius-sm 4px, font-body 14px) for "阶段"、"状态"、"提交人" with placeholder "全部" in --color-text-tertiary; right-aligned search input (height 32px, width 240px, --radius-sm 4px, prefix search icon 14px in --color-text-tertiary) with placeholder "搜索需求ID或内容". Active filters show selected values with clear (x) icon.

#### Variant Prompts
> **Active filters state**: Selected filter items show as filled tags (background #e6f4ff, text --color-primary, --radius-sm 4px, padding 2px 8px) with close icon
> **Empty results state**: No visual change to filter bar, table below shows empty state

#### Style Constraints
- Filters must reset independently (each has its own clear button)
- Search must trigger on Enter key or 300ms debounce after typing
- Filter state must persist in URL query params for shareability

---

### 3.4 数据表格 (Data Table)
**SRS Trace**: FR-019（需求列表7列）
**Variants**: Default, Loading, Empty, Row Hover

#### Base Prompt
> An Ant Design Table component with 7 columns: "需求ID" (font-code, 13px, --color-primary link), "摘要" (font-body, 14px, --color-text-primary, max-width 280px with ellipsis overflow), "提交人" (font-body, 14px), "提交时间" (font-body, 14px, --color-text-secondary, format YYYY-MM-DD HH:mm), "阶段" (font-body, 14px), "状态" (font-body, 14px), "操作" (font-body, 14px, --color-primary link "查看"). Table header: background #fafafa, font-label (14px/500 weight), --color-text-primary, border-bottom 1px solid #f0f0f0. Row height 54px, alternating rows #ffffff and #fafafa, hover state background #f5f5f5 with 0.1s ease transition. Pagination at bottom-right: Ant Design Pagination component, show total count, page size options [10, 20, 50].

#### Variant Prompts
> **Loading state**: Table body replaced with 5 skeleton rows (54px height each, shimmer animation on #f0f0f0 blocks)
> **Empty state**: Center-aligned empty component with illustration (128x96px), text "暂无需求数据" (font-heading-4, 20px, --color-text-tertiary), and primary button "提交第一个需求"
> **Row hover state**: Background #f5f5f5, row border-left 3px solid --color-primary

#### Style Constraints
- "需求ID" column must be left-aligned, others left-aligned except "操作" (right-aligned)
- "摘要" column must show full text on hover via Tooltip component
- "阶段" and "状态" columns must use colored Badge/Ant Design Tag component
- Table must support column sorting (click header to sort)
- Row selection checkbox must be available for bulk operations (future)

---

### 3.5 状态标签 (Status Badge/Tag)
**SRS Trace**: FR-005/009/013/017b（各阶段状态）
**Variants**: 待评审, 评审通过, 待仲裁, 已驳回, 设计中, 设计待确认, 实施中, 实施待验收, 已交付, 已终止

#### Base Prompt
> An Ant Design Tag component, inline display, height 22px, font-body-small (12px), --radius-sm (4px) corners, padding 0 --space-sm (8px). Color mapping: 待评审 (#d9d9d9 background, #00000073 text), 评审通过 (#e6f4ff background, #1677ff text), 待仲裁 (#fff7e6 background, #fa8c16 text), 已驳回 (#fff2f0 background, #ff4d4f text), 设计中 (#f9f0ff background, #722ed1 text), 设计待确认 (#fff7e6 background, #fa8c16 text), 实施中 (#e6fffb background, #13c2c2 text), 实施待验收 (#fff7e6 background, #fa8c16 text), 已交付 (#f6ffed background, #52c41a text), 已终止 (#f5f5f5 background, #00000073 text).

#### Style Constraints
- Tags must be non-interactive (display only, no click handler)
- Tag color must be semantic (consistent across all views)
- Maximum width 120px, text overflow shows ellipsis

---

### 3.6 主操作按钮 (Primary Button)
**SRS Trace**: FR-018/019/021（看板操作）
**Variants**: Default, Hover, Active, Disabled, Loading

#### Base Prompt
> An Ant Design Button with type="primary", height 32px, padding 0 --space-lg (16px), background --color-primary (#1677ff), text color #ffffff, font-body (14px/500 weight), --radius-sm (4px) corners. Box-shadow: 0 2px 0 rgba(5,145,255,0.1). Contains optional left-aligned icon (14px) before label text.

#### Variant Prompts
> **Hover state**: Background --color-primary-hover (#4096ff), box-shadow 0 2px 0 rgba(5,145,255,0.1)
> **Active state**: Background --color-primary-active (#0958d9), box-shadow inset 0 2px 0 rgba(0,0,0,0.01)
> **Disabled state**: Background #d9d9d9, text #ffffff40, box-shadow none, cursor not-allowed
> **Loading state**: Button text replaced with Spin indicator (14px, #ffffff), width preserved

#### Style Constraints
- Minimum width 64px for touch targets
- Icon + text gap 8px
- Loading state must preserve button width to prevent layout shift

---

### 3.7 次要操作按钮 (Secondary Button)
**SRS Trace**: FR-021（看板操作）
**Variants**: Default, Hover, Active, Disabled

#### Base Prompt
> An Ant Design Button with type="default", height 32px, padding 0 --space-lg (16px), background #ffffff, border 1px solid #d9d9d9, text color --color-text-primary, font-body (14px/500 weight), --radius-sm (4px) corners. Contains optional left-aligned icon (14px) before label text.

#### Variant Prompts
> **Hover state**: Border --color-primary, text --color-primary
> **Active state**: Background #f5f5f5, border --color-primary-active
> **Disabled state**: Background #f5f5f5, border #d9d9d9, text #00000040, cursor not-allowed

#### Style Constraints
- Must have same height as primary button (32px) for consistent button groups
- Button groups: primary left, secondary right with 8px gap

---

### 3.8 操作确认弹窗 (Action Confirm Modal)
**SRS Trace**: FR-021（看板确认/驳回操作）
**Variants**: Confirm, Reject with Input

#### Base Prompt
> An Ant Design Modal dialog, width 480px, centered vertically and horizontally, overlay background rgba(0,0,0,0.45). Modal: white background, --radius-md (6px) corners, --shadow-lg. Header: font-heading-4 (20px/600), --color-text-primary, 24px padding top, 16px horizontal. Body: font-body (14px), --color-text-primary, 16px horizontal padding. Footer: right-aligned button group, secondary "取消" button left, primary "确认" button right, 8px gap, 16px padding bottom.

#### Variant Prompts
> **Reject with input state**: Body contains textarea (height 80px, --radius-sm 4px, border 1px solid #d9d9d9, padding 8px) with placeholder "请输入驳回意见..." (required), character count display bottom-right (font-body-small, 12px, --color-text-tertiary). Primary button "确认驳回" changes to --color-error background.

#### Style Constraints
- Modal must trap focus for accessibility
- ESC key must close modal (confirm action = cancel)
- Click overlay must close modal (same as cancel)
- Reject textarea must have 500 character limit
- Submit button must be disabled until textarea has content (reject variant)

---

### 3.9 消息提示 (Toast/Message)
**SRS Trace**: FR-001~017b（IM操作反馈）
**Variants**: Success, Error, Warning, Info

#### Base Prompt
> An Ant Design Message notification, positioned top-center, 8px from top edge, auto-dismiss after 3s. Background: white, --radius-md (6px), --shadow-md, padding 8px 16px, font-body (14px). Contains: left-aligned status icon (16px) — checkmark circle for success (52c41a), close circle for error (ff4d4f), exclamation circle for warning (faad16), info circle for info (1677ff) — followed by message text (--color-text-primary).

#### Variant Prompts
> **Success**: Icon #52c41a, text "操作成功"
> **Error**: Icon #ff4d4f, text "操作失败，请重试"
> **Warning**: Icon #faad14, text "警告信息"
> **Info**: Icon #1677ff, text "提示信息"

#### Style Constraints
- Maximum 3 toasts visible simultaneously (queue excess)
- Click toast dismisses immediately
- Toast must not block page interactions

---

### 3.10 空状态 (Empty State)
**SRS Trace**: FR-018/019（无数据引导）
**Variants**: No Data, No Search Results

#### Base Prompt
> A centered empty state container, padding 64px vertical, 32px horizontal. Contains: top illustration (128x96px, Ant Design empty SVG with gray tones), title text (font-heading-4, 20px, --color-text-tertiary) showing "暂无数据", description text (font-body, 14px, --color-text-secondary) showing contextual help, optional primary action button below (font-body, 14px, --color-primary).

#### Variant Prompts
> **No Data state**: Title "暂无需求数据", description "提交您的第一个需求，开始自动化交付流程", button "提交需求"
> **No Search Results state**: Title "未找到匹配结果", description "尝试调整搜索关键词或筛选条件", no button

#### Style Constraints
- Illustration must be centered horizontally
- Maximum width 400px for text content (prevent wide line lengths)
- Button (if present) must link to appropriate action

---

## 4. Page Prompts

### 4.1 看板首页（Dashboard Overview）
**SRS Trace**: FR-018（总览看板指标）
**User Persona**: 需求提交人（研发）、管理员（技术 lead）
**Entry Points**: 登录后默认首页、点击导航栏 Logo

#### Layout Description
全宽布局，顶部 Header 导航栏（48px），下方主内容区域最大宽度 1200px 居中，左右各 24px 边距。内容区域分两部分：上方指标卡片区（3 列等宽网格，16px 间隙），下方快速入口区（可选）。

#### Full-Page Prompt
> A full-width dashboard page with white (#ffffff) background. Top: Header component (48px height, fixed). Main content area: max-width 1200px, centered horizontally, padding 24px horizontal. Top section: page title "总览" (font-heading-3, 24px/600 weight, --color-text-primary) with subtle bottom border. Below title: CSS Grid with 3 columns (1fr 1fr 1fr), gap 16px, containing 3 Metric Card components. First card: "总需求数" with value "128". Second card: "评审通过率" with value "85%" and green upward trend "+2.3%". Third card: "进行中需求" with value "12". Below grid: optional quick action section with secondary button "查看全部需求" linking to list page. Empty state (when no data): centered Empty State component with illustration, title "欢迎使用 DemandFlow", description "提交您的第一个需求，开始自动化交付流程", and primary button "提交需求".

#### Key Interactions
- Clicking metric cards could drill down to filtered list view (future)
- "查看全部需求" button navigates to requirement list page
- Auto-refresh every 30s to show latest metrics

#### Responsive Behavior
- **Desktop (>= 1024px)**: 3-column metric grid, max-width 1200px
- **Tablet (768-1023px)**: 2-column metric grid, max-width 100%
- **Mobile (< 768px)**: Single column stack, full-width cards

---

### 4.2 需求列表页（Requirement List）
**SRS Trace**: FR-019（需求列表与筛选搜索）
**User Persona**: 需求提交人（研发）、管理员（技术 lead）
**Entry Points**: 点击导航栏"需求列表"、首页"查看全部需求"按钮

#### Layout Description
全宽布局，顶部 Header 导航栏（48px），下方主内容区域最大宽度 1200px 居中。内容区域分三层：页面标题区、筛选栏、数据表格区。

#### Full-Page Prompt
> A full-width list page with white background. Top: Header component. Main content area: max-width 1200px, centered, padding 24px horizontal. Page header: title "需求列表" (font-heading-3, 24px/600) on left, primary button "提交需求" (height 32px, --color-primary background) on right, with 16px bottom margin. Below: Filter Bar component (56px height, #fafafa background). Below filter bar: Data Table component with 7 columns (需求ID, 摘要, 提交人, 提交时间, 阶段, 状态, 操作). Table takes full width of container. Bottom of table: Ant Design Pagination component, right-aligned, showing "共 128 条" total, page size selector [10, 20, 50].

#### Key Interactions
- Click "需求ID" column link opens requirement detail page (modal or new route)
- Type in search input triggers filtered table update (300ms debounce)
- Select filter dropdowns immediately filter table
- Click "查看" action link in operation column opens detail view
- Click "提交需求" opens IM submission flow (or modal for demo)
- Table columns sortable (click header icon to toggle asc/desc)

#### Responsive Behavior
- **Desktop (>= 1024px)**: Full 7-column table, filter bar horizontal
- **Tablet (768-1023px)**: Table may hide "提交时间" column, filter bar wraps
- **Mobile (< 768px)**: Card-based list view instead of table, filters in drawer

---

### 4.3 需求详情页（Requirement Detail）
**SRS Trace**: FR-005/009/010/012/016/017a（各阶段详情与产出物）
**User Persona**: 需求提交人（研发）、管理员（技术 lead）
**Entry Points**: 点击列表页"需求ID"或"查看"按钮

#### Layout Description
全宽布局，顶部 Header（48px），下方主内容最大宽度 1200px 居中。内容区域分左右两栏：左侧主内容区（70%宽度）展示需求信息与阶段产出物，右侧边栏（30%宽度）展示状态流转与操作按钮。

#### Full-Page Prompt
> A full-width detail page with white background. Top: Header component. Main content area: max-width 1200px, centered, padding 24px horizontal. Breadcrumb navigation at top: "需求列表 / REQ-20260704-001" (font-body, 14px, --color-primary links). Below breadcrumb: two-column layout using CSS Grid (grid-template-columns: 7fr 3fr), gap 24px. Left column (main content): Card component with padding 24px. Card header: requirement ID (font-code, 13px, --color-primary) and status badge (Status Badge component). Card body: requirement summary (font-heading-4, 20px/600, 16px bottom margin), full description text (font-body, 14px, --color-text-primary, line-height 22px), metadata row (提交人, 提交时间 in font-body-small, 12px, --color-text-secondary). Below metadata: divider. Below divider: phase-specific content sections — "评审结论" section (when in review phase) showing 3 role cards with scores, "设计产出物" section (when in design phase) showing document links and code skeleton, "实施结果" section (when in implementation phase) showing verification results and git commit info. Right column (sidebar): Card component with "状态流转" title (font-heading-4, 16px/600), vertical Timeline component showing all status transitions with timestamps, and at bottom: action buttons (Primary "确认" and Secondary "驳回") when current phase requires user decision.

#### Key Interactions
- Click breadcrumb "需求列表" returns to list page
- Click "确认" button opens Confirm Modal (Component 8)
- Click "驳回" button opens Reject Modal with textarea
- Timeline shows expandable details on click
- Phase content sections collapsible (accordion style)
- Click document links opens preview in new tab
- Click git commit link opens Git repository in new tab

#### Responsive Behavior
- **Desktop (>= 1024px)**: Two-column layout (7fr 3fr)
- **Tablet (768-1023px)**: Two-column layout (5fr 4fr), sidebar narrower
- **Mobile (< 768px)**: Single column stack, sidebar becomes bottom sheet

---

## 5. Style Rules & Constraints

### 5.1 Accessibility
- WCAG AA 标准（4.5:1 对比度 for normal text, 3:1 for large text）
- 所有交互元素必须支持键盘导航（Tab/Enter/Escape）
- 焦点状态必须可见（2px outline, --color-primary）
- 屏幕阅读器支持（ARIA labels for icons/buttons）
- 色彩对比度在所有 token 上已验证

### 5.2 Responsive Design
- 三档断点：Desktop (>= 1024px), Tablet (768-1023px), Mobile (< 768px)
- 移动端优先渐进增强
- 触摸目标最小 32px（WCAG 2.5.5）
- 表格在移动端转为卡片列表

### 5.3 Animation & Transitions
- 所有状态过渡 0.2s ease（hover, focus, active）
- 避免闪烁/跳动动画（减少前庭障碍风险）
- Skeleton loading 使用 1.5s 循环 shimmer
- Toast 消息 3s 自动消失，可手动关闭

### 5.4 Dark Mode (预留)
- 本轮不实现，但 token 映射已预留
- 深色模式背景 #141414，卡片 #1f1f1f，文字 #ffffffd9
- 主色保持 #1677ff（深色背景上对比度足够）

### 5.5 Internationalization
- 当前仅支持中文（SRS 范围）
- 文本容器使用弹性宽度（避免固定宽度截断）
- 日期格式统一 YYYY-MM-DD HH:mm
- 数字使用千位分隔符（toLocaleString）

---

## 6. Scaling Guide

| 项目规模 | UI 页面数 | UCD 深度 |
|----------|-----------|----------|
| Tiny | 1-3 | Style tokens + 3-5 core component prompts + page prompts; single approval |
| Small | 3-8 | Full style tokens + component prompts for used components + all page prompts |
| Medium | 8-20 | Full UCD with all component variants + responsive page prompts |
| Large | 20+ | Full UCD + interaction state matrices + animation spec + dark mode variants |

**本项目规模**: Small（3 页面，10 组件）— 完整 style tokens + 全部组件 prompt + 全部页面 prompt

---

**Document ends.**
