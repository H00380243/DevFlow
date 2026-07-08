import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RequirementDetailPage } from './RequirementDetailPage'

beforeEach(() => {
  vi.restoreAllMocks()
})

function renderWithRoute(id = 'REQ-001') {
  return render(
    <MemoryRouter initialEntries={[`/requirements/${id}`]}>
      <Routes>
        <Route path="/requirements/:id" element={<RequirementDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

const mockDetail = {
  id: 'REQ-20260709-0001',
  summary: '测试需求详情',
  original_text: '用户想要一个登录页面',
  submitter_id: 'user001',
  submitter_name: '张三',
  tags: ['前端', '紧急'],
  estimated_scope: '3人天',
  created_at: '2026-07-09T10:00:00',
  updated_at: '2026-07-09T12:00:00',
  current_stage: 'review',
  current_status: 'PENDING_REVIEW',
  review_count: 2,
  design_count: 0,
  implementation_count: 0,
  review_details: [
    { agent_role: '产品分析', business_value: 4, technical_feasibility: 5, roi: 3, system_compatibility: 4, verdict: '通过', comments: '好', scored_at: '2026-07-09T11:00:00' },
  ],
  design_details: [],
  implementation_details: [],
  timeline: [
    { from_status: null, to_status: 'PENDING_REVIEW', trigger_event: 'SUBMIT', trigger_user: 'user001', triggered_at: '2026-07-09T10:00:00' },
  ],
}

describe('RequirementDetailPage', () => {
  it('renders requirement ID and summary', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockDetail), { headers: { 'Content-Type': 'application/json' } })
    )
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('REQ-20260709-0001')).toBeInTheDocument()
      expect(screen.getByText('测试需求详情')).toBeInTheDocument()
    })
  })

  it('renders timeline section', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockDetail), { headers: { 'Content-Type': 'application/json' } })
    )
    const { container } = renderWithRoute()
    await waitFor(() => {
      expect(container.querySelector('.ant-timeline')).toBeInTheDocument()
    })
  })

  it('renders tags', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockDetail), { headers: { 'Content-Type': 'application/json' } })
    )
    const { container } = renderWithRoute()
    await waitFor(() => {
      const tags = container.querySelectorAll('.ant-tag')
      expect(tags.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('renders stage and status badges', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockDetail), { headers: { 'Content-Type': 'application/json' } })
    )
    const { container } = renderWithRoute()
    await waitFor(() => {
      expect(container.querySelectorAll('.ant-badge').length).toBeGreaterThanOrEqual(2)
    })
  })

  it('renders error state when fetch fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('API error'))
    renderWithRoute('nonexistent')
    await waitFor(() => {
      expect(screen.getByText('加载失败')).toBeInTheDocument()
    })
  })

  it('renders newly created requirement with empty relations', async () => {
    const emptyDetail = {
      id: 'REQ-20260708-001',
      summary: '新建需求',
      original_text: '描述内容',
      submitter_id: 'user001',
      submitter_name: '张三',
      tags: [],
      estimated_scope: null,
      created_at: '2026-07-08T10:00:00',
      updated_at: '2026-07-08T10:00:00',
      current_stage: 'review',
      current_status: 'PENDING_REVIEW',
      review_count: 0,
      design_count: 0,
      implementation_count: 0,
      review_details: [],
      design_details: [],
      implementation_details: [],
      timeline: [],
    }
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(emptyDetail), { headers: { 'Content-Type': 'application/json' } })
    )
    const { container } = renderWithRoute('REQ-20260708-001')
    await waitFor(() => {
      expect(screen.getByText('REQ-20260708-001')).toBeInTheDocument()
    })
    expect(screen.getByText('暂无流转记录')).toBeInTheDocument()
    expect(screen.getByText('新建需求')).toBeInTheDocument()
    expect(container.querySelectorAll('.ant-descriptions-item').length).toBeGreaterThan(0)
  })
})
