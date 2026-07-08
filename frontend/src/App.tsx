import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { DashboardPage } from './pages/DashboardPage'
import { RequirementsListPage } from './pages/RequirementsListPage'

function App() {
  return (
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/requirements" element={<RequirementsListPage />} />
          </Routes>
        </div>
      </ConfigProvider>
    </BrowserRouter>
  )
}

export default App
