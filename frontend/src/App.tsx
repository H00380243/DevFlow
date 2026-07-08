import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { DashboardPage } from './pages/DashboardPage'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
        <DashboardPage />
      </div>
    </ConfigProvider>
  )
}

export default App
