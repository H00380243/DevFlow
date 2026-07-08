import { useEffect, useState, useCallback } from 'react'
import { Table, Select, Input, Empty, message, Row, Col } from 'antd'
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
  const [data, setData] = useState<PageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [stage, setStage] = useState<string | undefined>()
  const [status, setStatus] = useState<string | undefined>()
  const [search, setSearch] = useState('')

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
      </Row>
      {data && data.items.length === 0 && !loading ? (
        <Empty description="暂无匹配需求" />
      ) : (
        <Table
          columns={columns}
          dataSource={data?.items ?? []}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: 10,
            total: data?.total ?? 0,
            onChange: setPage,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      )}
    </div>
  )
}
