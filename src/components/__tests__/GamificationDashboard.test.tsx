import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import GamificationDashboard from '../GamificationDashboard'
import * as ccmApi from '@/lib/ccm-api'

vi.mock('@/lib/ccm-api')
const mockedCcmApi = vi.mocked(ccmApi)

const mockDashboardData = {
  success: true,
  dashboard: {
    user_stats: {
      id: 'test-user',
      username: 'testuser',
      total_xp: 1500,
      level: 5,
      current_streak: 7,
      longest_streak: 15,
      total_commits: 42,
      total_flow_time: 300
    },
    achievements: [
      {
        id: 'first-commit',
        name: 'First Commit',
        description: 'Made your first commit',
        icon: 'trophy',
        unlocked_at: '2024-01-01T00:00:00Z'
      }
    ],
    leaderboards: {
      xp: [
        { username: 'user1', total_xp: 2000, level: 6 },
        { username: 'testuser', total_xp: 1500, level: 5 }
      ],
      streaks: [
        { username: 'user2', current_streak: 10 },
        { username: 'testuser', current_streak: 7 }
      ]
    }
  }
}

describe('GamificationDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockedCcmApi.getGamificationDashboard.mockImplementation(() => new Promise(() => {}))
    
    render(<GamificationDashboard />)
    
    expect(screen.getByText('Loading gamification data...')).toBeInTheDocument()
  })

  it('renders dashboard data successfully', async () => {
    mockedCcmApi.getGamificationDashboard.mockResolvedValue(mockDashboardData)
    
    render(<GamificationDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Gamification Dashboard')).toBeInTheDocument()
    })

    // Check user stats
    expect(screen.getByText('Level 5')).toBeInTheDocument()
    expect(screen.getByText('1,500 XP')).toBeInTheDocument()
    expect(screen.getByText('7 days')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()

    // Check achievements
    expect(screen.getByText('Achievements')).toBeInTheDocument()
    expect(screen.getByText('First Commit')).toBeInTheDocument()

    // Check leaderboards
    expect(screen.getByText('XP Leaderboard')).toBeInTheDocument()
    expect(screen.getByText('Streak Leaderboard')).toBeInTheDocument()
  })

  it('handles API error gracefully', async () => {
    mockedCcmApi.getGamificationDashboard.mockRejectedValue(new Error('API Error'))
    
    render(<GamificationDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading gamification data. Please try again.')).toBeInTheDocument()
    })
  })

  it('calls API with correct session ID', async () => {
    mockedCcmApi.getGamificationDashboard.mockResolvedValue(mockDashboardData)
    
    render(<GamificationDashboard />)
    
    await waitFor(() => {
      expect(mockedCcmApi.getGamificationDashboard).toHaveBeenCalledWith('default-session')
    })
  })

  it('displays achievement unlock dates correctly', async () => {
    mockedCcmApi.getGamificationDashboard.mockResolvedValue(mockDashboardData)
    
    render(<GamificationDashboard />)
    
    await waitFor(() => {
      expect(screen.getByText('Unlocked: January 1, 2024')).toBeInTheDocument()
    })
  })
})