import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { RequirementsListPage } from './RequirementsListPage'

beforeEach(() => {
  vi.restoreAllMocks()
})

function mockFetch(items: any[] = [], total = 0) {
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
    new Response(JSON.stringify({ items, total, page: 1, page_size: 10 }), {
      headers: { 'Content-Type': 'application/json' },
    })
  )
}

describe('RequirementsListPage', () => {
  it('renders page title', async () => {
    mockFetch()
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('需求列表')).toBeInTheDocument()
    })
  })

  it('renders filter selects', async () => {
    mockFetch()
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(container.querySelectorAll('.ant-select').length).toBeGreaterThanOrEqual(2)
    })
  })

  it('renders add requirement button', async () => {
    mockFetch()
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('添加需求')).toBeInTheDocument()
    })
  })

  it('opens modal on button click', async () => {
    mockFetch()
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    const btn = await screen.findByText('添加需求')
    await userEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText('需求描述')).toBeInTheDocument()
    })
  })

  it('renders table with 7 columns', async () => {
    mockFetch([{
      id: 'REQ-001', summary: 'test', submitter_name: 'user1',
      created_at: '2026-07-09T00:00:00', current_stage: 'review', current_status: 'PENDING_REVIEW',
    }])
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      const headers = container.querySelectorAll('.ant-table-thead th')
      expect(headers.length).toBe(7)
    })
  })

  it('renders action buttons for actionable status', async () => {
    mockFetch([{
      id: 'REQ-001', summary: 'test', submitter_name: 'user1',
      created_at: '2026-07-09T00:00:00', current_stage: 'review', current_status: 'PENDING_REVIEW',
    }])
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('确认')).toBeInTheDocument()
      expect(screen.getByText('驳回')).toBeInTheDocument()
    })
  })

  it('does not render action buttons for non-actionable status', async () => {
    mockFetch([{
      id: 'REQ-002', summary: 'test2', submitter_name: 'user1',
      created_at: '2026-07-09T00:00:00', current_stage: 'implementation', current_status: 'IN_IMPLEMENTATION',
    }])
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.queryByText('确认')).not.toBeInTheDocument()
      expect(screen.queryByText('驳回')).not.toBeInTheDocument()
    })
  })

  it('calls confirm action API on button click', async () => {
    mockFetch([{
      id: 'REQ-001', summary: 'test', submitter_name: 'user1',
      created_at: '2026-07-09T00:00:00', current_stage: 'review', current_status: 'PENDING_REVIEW',
    }])
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ status: 'ok', message: '已确认' }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )

    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    const confirmBtn = await screen.findByText('确认')
    await userEvent.click(confirmBtn)

    await waitFor(() => {
      expect(screen.getByText('已确认')).toBeInTheDocument()
    })
  })

  it('opens reject modal with reason field', async () => {
    mockFetch([{
      id: 'REQ-001', summary: 'test', submitter_name: 'user1',
      created_at: '2026-07-09T00:00:00', current_stage: 'review', current_status: 'PENDING_REVIEW',
    }])
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    const rejectBtn = await screen.findByText('驳回')
    await userEvent.click(rejectBtn)

    await waitFor(() => {
      expect(screen.getByText('驳回需求')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('请输入驳回原因（必填）')).toBeInTheDocument()
    })
  })

  it('renders pagination with total > page_size', async () => {
    const items = Array.from({ length: 10 }, (_, i) => ({
      id: `REQ-00${i}`, summary: `test${i}`, submitter_name: 'user1',
      created_at: '2026-07-09T00:00:00', current_stage: 'review', current_status: 'PENDING_REVIEW',
    }))
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ items, total: 25, page: 1, page_size: 10 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(container.querySelector('.ant-pagination')).toBeInTheDocument()
    })
  })

  it('renders empty state when no items', async () => {
    mockFetch()
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(container.querySelector('.ant-empty')).toBeInTheDocument()
    })
  })
})
