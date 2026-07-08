import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Descriptions, Tag, Timeline, Badge, Card, Row, Col, Skeleton, Result, Button, Modal, Input, message } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'

interface TimelineEntry {
  from_status: string | null
  to_status: string | null
  trigger_event: string | null
  trigger_user: string | null
  triggered_at: string | null
}

interface ReviewDetail {
  agent_role: string
  business_value: number
  technical_feasibility: number
  roi: number
  system_compatibility: number
  verdict: string
  comments: string | null
  scored_at: string | null
}

interface DesignDetail {
  agent_role: string
  document_url: string | null
  skeleton_dirs: string[]
  core_interfaces: string[]
  risk_warnings: string[]
  created_at: string | null
  version: number
}

interface ImplementationDetail {
  code_files: { path: string; lines: number }[]
  verification_result: object | null
  branch_name: string | null
  commit_id: string | null
  commit_message: string | null
  committed_at: string | null
}

interface DetailData {
  id: string
  summary: string | null
  original_text: string
  submitter_id: string
  submitter_name: string | null
  tags: string[]
  estimated_scope: string | null
  created_at: string | null
  updated_at: string | null
  current_stage: string
  current_status: string
  review_count: number
  design_count: number
  implementation_count: number
  review_details: ReviewDetail[]
  design_details: DesignDetail[]
  implementation_details: ImplementationDetail[]
  timeline: TimelineEntry[]
}

const statusColorMap: Record<string, string> = {
  PENDING_REVIEW: 'orange',
  IN_REVIEW: 'processing',
  IN_DESIGN: 'purple',
  DESIGN_PENDING_CONFIRM: 'geekblue',
  DESIGN_CONFIRMED: 'blue',
  IN_IMPLEMENTATION: 'cyan',
  IMPL_PENDING_ACCEPTANCE: 'gold',
  IMPL_APPROVED: 'green',
  DELIVERED: 'green',
}

const stageLabelMap: Record<string, string> = {
  review: '评审中',
  design: '设计中',
  implementation: '实施中',
}

const ACTIONABLE_STATUSES = ['PENDING_REVIEW', 'DESIGN_PENDING_CONFIRM', 'IMPL_PENDING_ACCEPTANCE', 'PENDING_ARBITRATION']

export function RequirementDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<DetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rejectModalOpen, setRejectModalOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const fetchDetail = () => {
    if (!id) return
    setLoading(true)
    setError(null)
    fetch(`/api/requirements/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? '需求不存在' : '加载失败')
        return r.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchDetail() }, [id])

  const performAction = async (action: string, reason = '') => {
    setActionLoading(true)
    try {
      const resp = await fetch(`/api/requirements/${id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, reason, user_id: 'current-user' }),
      })
      const result = await resp.json()
      if (result.status === 'ok') {
        message.success(result.message)
        setRejectModalOpen(false)
        setRejectReason('')
        fetchDetail()
      } else {
        message.error(result.message)
      }
    } catch {
      message.error('操作失败')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <Skeleton active paragraph={{ rows: 8 }} />
  if (error) return <Result status="error" title="加载失败" subTitle={error} extra={<Button type="primary" onClick={() => window.history.back()}>返回</Button>} />
  if (!data) return null

  const isActionable = ACTIONABLE_STATUSES.includes(data.current_status)

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate('/requirements')} style={{ padding: 0, marginBottom: 16 }}>
        返回列表
      </Button>
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: 16 }}>
        {isActionable && (
          <div style={{ display: 'flex', gap: 8 }}>
            <Button type="primary" loading={actionLoading} onClick={() => performAction('confirm')}>
              确认
            </Button>
            <Button danger loading={actionLoading} onClick={() => setRejectModalOpen(true)}>
              驳回
            </Button>
          </div>
        )}
      </div>
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card title="需求信息" variant="outlined">
            <Descriptions column={1} size="small" styles={{ label: { fontWeight: 500 } }}>
              <Descriptions.Item label="ID">{data.id}</Descriptions.Item>
              <Descriptions.Item label="摘要">{data.summary || '-'}</Descriptions.Item>
              <Descriptions.Item label="原始内容">{data.original_text}</Descriptions.Item>
              <Descriptions.Item label="提交人">{data.submitter_name || data.submitter_id}</Descriptions.Item>
              <Descriptions.Item label="预估范围">{data.estimated_scope || '-'}</Descriptions.Item>
              <Descriptions.Item label="阶段">
                <Badge status="default" text={stageLabelMap[data.current_stage] || data.current_stage} />
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Badge status={(statusColorMap[data.current_status] || 'default') as any} text={data.current_status} />
              </Descriptions.Item>
              <Descriptions.Item label="标签">
                {data.tags.length > 0
                  ? data.tags.map((t) => <Tag key={t}>{t}</Tag>)
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">{data.created_at ? new Date(data.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{data.updated_at ? new Date(data.updated_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
              <Descriptions.Item label="评审次数">{data.review_count}</Descriptions.Item>
              <Descriptions.Item label="设计次数">{data.design_count}</Descriptions.Item>
              <Descriptions.Item label="实施次数">{data.implementation_count}</Descriptions.Item>
            </Descriptions>
          </Card>

          {data.design_details.length > 0 && (
            <Card title="设计文档" variant="outlined" style={{ marginTop: 16 }}>
              {data.design_details.map((dd, i) => (
                <div key={i} style={{ marginBottom: i < data.design_details.length - 1 ? 16 : 0 }}>
                  <Descriptions column={1} size="small" styles={{ label: { fontWeight: 500 } }}>
                    <Descriptions.Item label="设计角色">{dd.agent_role}</Descriptions.Item>
                    <Descriptions.Item label="版本">{dd.version}</Descriptions.Item>
                    <Descriptions.Item label="时间">{dd.created_at ? new Date(dd.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
                    <Descriptions.Item label="文档链接">{dd.document_url || '-'}</Descriptions.Item>
                    <Descriptions.Item label="目录结构">
                      {dd.skeleton_dirs.length > 0
                        ? dd.skeleton_dirs.map((d) => <Tag key={d}>{d}</Tag>)
                        : '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="核心接口">
                      {dd.core_interfaces.length > 0
                        ? dd.core_interfaces.map((c) => <div key={c} style={{ fontFamily: 'monospace', fontSize: 12 }}>{c}</div>)
                        : '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="风险警告">
                      {dd.risk_warnings.length > 0
                        ? dd.risk_warnings.map((w, j) => (
                            <Tag key={j} color={w.includes('高风险') ? 'red' : 'orange'}>{w}</Tag>
                          ))
                        : '无'}
                    </Descriptions.Item>
                  </Descriptions>
                  {i < data.design_details.length - 1 && <hr style={{ opacity: 0.2 }} />}
                </div>
              ))}
            </Card>
          )}

          {data.review_details.length > 0 && (
            <Card title="评审详情" variant="outlined" style={{ marginTop: 16 }}>
              {data.review_details.map((rd, i) => (
                <div key={i} style={{ marginBottom: i < data.review_details.length - 1 ? 16 : 0 }}>
                  <Descriptions column={2} size="small" styles={{ label: { fontWeight: 500 } }}>
                    <Descriptions.Item label="评审角色">{rd.agent_role}</Descriptions.Item>
                    <Descriptions.Item label="裁决">
                      <Tag color={rd.verdict === '通过' ? 'green' : rd.verdict === '反对' ? 'red' : 'orange'}>{rd.verdict}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="商业价值">{rd.business_value}</Descriptions.Item>
                    <Descriptions.Item label="技术可行性">{rd.technical_feasibility}</Descriptions.Item>
                    <Descriptions.Item label="ROI">{rd.roi}</Descriptions.Item>
                    <Descriptions.Item label="系统兼容性">{rd.system_compatibility}</Descriptions.Item>
                    <Descriptions.Item label="评语" span={2}>{rd.comments || '-'}</Descriptions.Item>
                  </Descriptions>
                  {i < data.review_details.length - 1 && <hr style={{ opacity: 0.2 }} />}
                </div>
              ))}
            </Card>
          )}

          {data.implementation_details.length > 0 && (
            <Card title="实施详情" variant="outlined" style={{ marginTop: 16 }}>
              {data.implementation_details.map((impl, i) => (
                <div key={i}>
                  <Descriptions column={1} size="small" styles={{ label: { fontWeight: 500 } }}>
                    <Descriptions.Item label="分支">{impl.branch_name || '-'}</Descriptions.Item>
                    <Descriptions.Item label="提交 ID">{impl.commit_id || '-'}</Descriptions.Item>
                    <Descriptions.Item label="提交信息">{impl.commit_message || '-'}</Descriptions.Item>
                    <Descriptions.Item label="提交时间">{impl.committed_at ? new Date(impl.committed_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
                    <Descriptions.Item label="代码文件">
                      {impl.code_files.length > 0
                        ? impl.code_files.map((f, j) => <div key={j} style={{ fontFamily: 'monospace', fontSize: 12 }}>{f.path} ({f.lines} lines)</div>)
                        : '-'}
                    </Descriptions.Item>
                  </Descriptions>
                </div>
              ))}
            </Card>
          )}
        </Col>
        <Col xs={24} lg={8}>
          <Card title="状态流转记录" variant="outlined">
            {data.timeline.length === 0 ? (
              <span style={{ color: '#999' }}>暂无流转记录</span>
            ) : (
              <Timeline
                items={data.timeline.map((t) => ({
                  content: (
                    <div>
                      <div><strong>{t.to_status || '-'}</strong></div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {t.trigger_event && `${t.trigger_event} — `}{t.trigger_user || '-'}
                      </div>
                      <div style={{ fontSize: 12, color: '#999' }}>
                        {t.triggered_at ? new Date(t.triggered_at).toLocaleString('zh-CN') : '-'}
                      </div>
                    </div>
                  ),
                }))}
              />
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title="驳回原因"
        open={rejectModalOpen}
        onOk={() => performAction('reject', rejectReason)}
        onCancel={() => { setRejectModalOpen(false); setRejectReason('') }}
        confirmLoading={actionLoading}
        okText="确认驳回"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <Input.TextArea
          rows={4}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="请输入驳回原因"
        />
      </Modal>
    </div>
  )
}
