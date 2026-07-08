import { Card, Skeleton, Tooltip, Tag } from 'antd'
import { WarningOutlined } from '@ant-design/icons'

interface MetricCardProps {
  label: string
  value: string | null
  loading?: boolean
  error?: string | null
}

export function MetricCard({ label, value, loading, error }: MetricCardProps) {
  return (
    <Card className="metric-card" size="small">
      <div className="metric-label" style={{ color: '#8c8c8c', fontSize: 14, marginBottom: 8 }}>
        {label}
      </div>
      {loading ? (
        <div className="metric-skeleton">
          <Skeleton.Input active size="small" />
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="metric-value" style={{ fontSize: 28, fontWeight: 600 }}>
            {value ?? '--'}
          </span>
          {error ? (
            <Tooltip title={error}>
              <Tag color="warning" className="metric-error-badge">
                <WarningOutlined /> 异常
              </Tag>
            </Tooltip>
          ) : null}
        </div>
      )}
    </Card>
  )
}
