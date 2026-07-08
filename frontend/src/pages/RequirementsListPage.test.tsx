import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { RequirementsListPage } from './RequirementsListPage'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('RequirementsListPage', () => {
  it('renders page title', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )
    render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('需求列表')).toBeInTheDocument()
    })
  })

  it('renders filter selects', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(container.querySelectorAll('.ant-select').length).toBeGreaterThanOrEqual(2)
    })
  })

  it('renders table with 7 columns', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          items: [{ id: 'REQ-001', summary: 'test', submitter_name: 'user1', created_at: '2026-07-09T00:00:00', current_stage: 'review', current_status: 'PENDING_REVIEW' }],
          total: 1,
          page: 1,
          page_size: 10,
        }),
        { headers: { 'Content-Type': 'application/json' } }
      )
    )
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      const headers = container.querySelectorAll('.ant-table-thead th')
      expect(headers.length).toBe(6)
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
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )
    const { container } = render(<MemoryRouter><RequirementsListPage /></MemoryRouter>)
    await waitFor(() => {
      expect(container.querySelector('.ant-empty')).toBeInTheDocument()
    })
  })
})
