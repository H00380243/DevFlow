import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { DashboardPage } from './DashboardPage'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('DashboardPage', () => {
  it('renders 3 metric cards with mock data', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ total_requirements: 10, review_pass_rate: 50.0, in_progress_count: 3 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument()
    })
    expect(screen.getByText('总需求数')).toBeInTheDocument()
    expect(screen.getByText('评审通过率')).toBeInTheDocument()
    expect(screen.getByText('进行中')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders empty state when total is 0', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ total_requirements: 0, review_pass_rate: null, in_progress_count: 0 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    )
    const { container } = render(<DashboardPage />)
    await waitFor(() => {
      expect(container.querySelector('.empty-state')).toBeInTheDocument()
    })
  })

  it('renders error badge on partial failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          total_requirements: 5,
          review_pass_rate: 60.0,
          in_progress_count: 3,
          errors: ['approved_count query failed'],
        }),
        { headers: { 'Content-Type': 'application/json' } }
      )
    )
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('异常')).toBeInTheDocument()
    })
  })

  it('shows loading skeleton initially', () => {
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {}))
    const { container } = render(<DashboardPage />)
    expect(container.querySelector('.metric-skeleton')).toBeInTheDocument()
  })
})
