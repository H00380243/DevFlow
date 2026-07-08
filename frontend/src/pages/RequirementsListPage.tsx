import { useEffect, useState, useCallback } from 'react'
import { Table, Select, Input, Empty, message, Row, Col, Button, Modal, Form } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { ColumnsType } from 'antd/es/table'

interface Requirement {
  id: string
  summary: string
  submitter_name: string
  created_at: string | null
  current_stage: string
  current_status: string
}

interface PageData {
  items: Requirement[]
  total: number
  page: number
  page_size: number
}

const columns: ColumnsType<Requirement> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 180 },
  { title: '摘要', dataIndex: 'summary', key: 'summary' },
  { title: '提交人', dataIndex: 'submitter_name', key: 'submitter_name', width: 120 },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180, render: (v: string | null) => v ? new Date(v).toLocaleDateString('zh-CN') : '-' },
  { title: '阶段', dataIndex: 'current_stage', key: 'current_stage', width: 120 },
  { title: '状态', dataIndex: 'current_status', key: 'current_status', width: 120 },
]

export function RequirementsListPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [stage, setStage] = useState<string | undefined>()
  const [status, setStatus] = useState<string | undefined>()
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm()

  const fetchData = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(page), page_size: '10' })
    if (stage) params.set('stage', stage)
    if (status) params.set('status', status)
    if (search) params.set('search', search)
    try {
      const resp = await fetch(`/api/requirements?${params}`)
      if (!resp.ok) throw new Error('加载失败')
      const json: PageData = await resp.json()
      setData(json)
    } catch {
      message.error('加载需求列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, stage, status, search])

  useEffect(() => { fetchData() }, [fetchData])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      const resp = await fetch('/api/requirements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || '创建失败')
      }
      message.success('需求创建成功')
      setModalOpen(false)
      form.resetFields()
      setPage(1)
      fetchData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="requirements-title" style={{ marginBottom: 24 }}>需求列表</h1>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Select
            placeholder="阶段"
            allowClear
            style={{ width: 140 }}
            onChange={(v) => { setStage(v); setPage(1) }}
            options={[
              { value: 'review', label: '评审' },
              { value: 'design', label: '设计' },
              { value: 'implementation', label: '实施' },
            ]}
          />
        </Col>
        <Col>
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 140 }}
            onChange={(v) => { setStatus(v); setPage(1) }}
            options={[
              { value: 'PENDING_REVIEW', label: '待评审' },
              { value: 'IN_DESIGN', label: '设计中' },
              { value: 'IN_IMPLEMENTATION', label: '实施中' },
            ]}
          />
        </Col>
        <Col>
          <Input.Search
            placeholder="搜索 ID 或摘要"
            onSearch={(v) => { setSearch(v); setPage(1) }}
            style={{ width: 240 }}
          />
        </Col>
        <Col>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            添加需求
          </Button>
        </Col>
      </Row>
      {data && data.items.length === 0 && !loading ? (
        <Empty description="暂无匹配需求" />
      ) : (
        <Table
          columns={columns}
          dataSource={data?.items ?? []}
          rowKey="id"
          loading={loading}
          onRow={(record) => ({ onClick: () => navigate(`/requirements/${record.id}`), style: { cursor: 'pointer' } })}
          pagination={{
            current: page,
            pageSize: 10,
            total: data?.total ?? 0,
            onChange: setPage,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      )}

      <Modal
        title="添加需求"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        confirmLoading={submitting}
        okText="创建"
        cancelText="取消"
        destroyOnHidden
      >
        <Form form={form} layout="vertical" autoComplete="off">
          <Form.Item name="original_text" label="需求描述" rules={[{ required: true, message: '请输入需求描述' }]}>
            <Input.TextArea rows={4} placeholder="请输入需求详细描述" />
          </Form.Item>
          <Form.Item name="summary" label="摘要" rules={[{ required: true, message: '请输入需求摘要' }]}>
            <Input placeholder="简短的需求摘要" />
          </Form.Item>
          <Form.Item name="submitter_id" label="提交人 ID" rules={[{ required: true, message: '请输入提交人 ID' }]}>
            <Input placeholder="user001" />
          </Form.Item>
          <Form.Item name="submitter_name" label="提交人姓名">
            <Input placeholder="显示名称（可选）" />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
