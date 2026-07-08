import { useEffect, useState } from 'react'
import { Empty, message, Row, Col, Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { MetricCard } from '../components/MetricCard'

interface Metrics {
  total_requirements: number
  review_pass_rate: number | null
  in_progress_count: number
  errors?: string[]
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [errors, setErrors] = useState<string[]>([])

  useEffect(() => {
    fetch('/api/dashboard/metrics')
      .then(async (res) => {
        if (!res.ok) throw new Error('加载指标失败')
        const json: Metrics = await res.json()
        setData(json)
        setErrors(json.errors ?? [])
      })
      .catch(() => {
        message.error('加载指标失败')
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <h1 className="dashboard-title" style={{ marginBottom: 24 }}>总览</h1>
        <Row gutter={[16, 16]}>
          <Col span={8}><MetricCard label="总需求数" value={null} loading /></Col>
          <Col span={8}><MetricCard label="评审通过率" value={null} loading /></Col>
          <Col span={8}><MetricCard label="进行中" value={null} loading /></Col>
        </Row>
      </div>
    )
  }

  if (!data || data.total_requirements === 0) {
    return (
      <div className="empty-state">
        <h1 className="dashboard-title" style={{ marginBottom: 24 }}>总览</h1>
        <Empty description="暂无需求数据" />
      </div>
    )
  }

  const rateStr = data.review_pass_rate != null ? `${data.review_pass_rate}%` : '--'
  const rateError = errors.length > 0 ? errors.join('; ') : undefined

  return (
    <div>
      <h1 className="dashboard-title" style={{ marginBottom: 24 }}>总览</h1>
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <MetricCard label="总需求数" value={String(data.total_requirements)} />
        </Col>
        <Col span={8}>
          <MetricCard label="评审通过率" value={rateStr} error={rateError ?? null} />
        </Col>
        <Col span={8}>
          <MetricCard label="进行中" value={String(data.in_progress_count)} />
        </Col>
      </Row>
      <Row style={{ marginTop: 24 }}>
        <Col>
          <Button type="primary" onClick={() => navigate('/requirements')}>
            查看全部需求
          </Button>
        </Col>
      </Row>
    </div>
  )
}
