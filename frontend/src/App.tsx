import { BrowserRouter, Routes, Route, useLocation, Link } from 'react-router-dom'
import { ConfigProvider, Menu } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { DashboardPage } from './pages/DashboardPage'
import { RequirementsListPage } from './pages/RequirementsListPage'
import { RequirementDetailPage } from './pages/RequirementDetailPage'

const navItems = [
  { key: '/', label: <Link to="/">总览</Link> },
  { key: '/requirements', label: <Link to="/requirements">需求列表</Link> },
]

function AppLayout() {
  const loc = useLocation()
  const activeKey = loc.pathname === '/' ? '/' : '/requirements'

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <Menu mode="horizontal" selectedKeys={[activeKey]} items={navItems} style={{ marginBottom: 24 }} />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/requirements" element={<RequirementsListPage />} />
        <Route path="/requirements/:id" element={<RequirementDetailPage />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        <AppLayout />
      </ConfigProvider>
    </BrowserRouter>
  )
}

export default App
