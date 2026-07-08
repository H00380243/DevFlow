import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MetricCard } from './MetricCard'

describe('MetricCard', () => {
  it('renders label and value', () => {
    render(<MetricCard label="总需求数" value="10" />)
    expect(screen.getByText('总需求数')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('renders null value as --', () => {
    render(<MetricCard label="评审通过率" value={null} />)
    expect(screen.getByText('--')).toBeInTheDocument()
  })

  it('renders loading skeleton', () => {
    const { container } = render(<MetricCard label="总需求数" loading />)
    expect(container.querySelector('.metric-skeleton')).toBeInTheDocument()
  })

  it('renders error badge', () => {
    render(<MetricCard label="评审通过率" value="50%" error="计算失败" />)
    expect(screen.getByText('异常')).toBeInTheDocument()
  })
})
