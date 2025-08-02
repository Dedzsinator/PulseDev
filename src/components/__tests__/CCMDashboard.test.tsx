import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@/test/utils'
import { ccmAPI } from '@/lib/ccm-api'
import CCMDashboard from '../CCMDashboard'

vi.mock('@/lib/ccm-api')
const mockedCcmApi = vi.mocked(ccmAPI)

describe('CCMDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders main dashboard components', () => {
    render(<CCMDashboard />)

    expect(screen.getByText('PulseDev+ Cognitive Context Mirror')).toBeInTheDocument()
    expect(screen.getByText('System Metrics')).toBeInTheDocument()
    expect(screen.getByText('CCM Features')).toBeInTheDocument()
    expect(screen.getByText('Context Event Form')).toBeInTheDocument()
  })

  it('allows switching between different tabs', () => {
    render(<CCMDashboard />)

    // Click on different tabs
    const gamificationTab = screen.getByText('Gamification')
    fireEvent.click(gamificationTab)

    expect(screen.getByText('Gamification Dashboard')).toBeInTheDocument()
  })

  it('shows correct tab navigation', () => {
    render(<CCMDashboard />)

    const tabs = ['System', 'Features', 'Events', 'Gamification']

    tabs.forEach(tab => {
      expect(screen.getByText(tab)).toBeInTheDocument()
    })
  })

  it('maintains active tab state', () => {
    render(<CCMDashboard />)

    const gamificationTab = screen.getByText('Gamification')
    fireEvent.click(gamificationTab)

    // Verify the tab is active (this would depend on your styling)
    expect(gamificationTab.closest('[data-state="active"]')).toBeInTheDocument()
  })
})