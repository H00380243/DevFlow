import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Descriptions, Tag, Timeline, Badge, Card, Row, Col, Skeleton, Result, Button, Modal, Input, message } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'

interface TimelineEntry {
  from_status: string | null
  to_status: string | null
  trigger_event: string | null
  trigger_user: string | null
  triggered_at: string | null
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => window.history.back()}>
          返回列表
        </Button>
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
