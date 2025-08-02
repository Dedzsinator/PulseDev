import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ccmAPI } from '../ccm-api'

// Mock the API module
const mockPost = vi.fn()
const mockGet = vi.fn()

vi.mock('../api', () => ({
  default: {
    post: mockPost,
    get: mockGet,
  }
}))

describe('CCM API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('storeContextEvent', () => {
    it('should submit context event successfully', async () => {
      const mockEvent = {
        sessionId: 'test-session',
        agent: 'vscode',
        type: 'file_edit',
        payload: { file: 'test.ts' },
        timestamp: new Date().toISOString()
      }

      const mockResponse = { data: { status: 'success', event_id: '123' } }
      mockPost.mockResolvedValue(mockResponse)

      const result = await ccmAPI.storeContextEvent(mockEvent)

      expect(mockPost).toHaveBeenCalledWith('/api/v1/context/events', mockEvent)
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle API error', async () => {
      const mockEvent = {
        sessionId: 'test-session',
        agent: 'vscode',
        type: 'file_edit',
        payload: { file: 'test.ts' },
        timestamp: new Date().toISOString()
      }

      mockPost.mockRejectedValue(new Error('API Error'))

      await expect(ccmAPI.storeContextEvent(mockEvent)).rejects.toThrow('API Error')
    })
  })

  describe('getGamificationDashboard', () => {
    it('should fetch gamification dashboard data', async () => {
      const sessionId = 'test-session'
      const mockResponse = {
        data: {
          success: true,
          dashboard: {
            user_stats: { level: 5, xp: 1000 },
            achievements: [],
            leaderboards: { xp: [], streaks: [] }
          }
        }
      }

      mockGet.mockResolvedValue(mockResponse)

      const result = await ccmAPI.getGamificationDashboard(sessionId)

      expect(mockGet).toHaveBeenCalledWith(`/api/v1/gamification/dashboard/${sessionId}`)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('awardXP', () => {
    it('should award XP successfully', async () => {
      const sessionId = 'test-session'
      const source = 'commit'
      const amount = 100
      const description = 'Test commit'

      const mockResponse = {
        data: { success: true, xp_earned: 100 }
      }

      mockPost.mockResolvedValue(mockResponse)

      const result = await ccmAPI.awardXP(sessionId, source, amount, { description })

      expect(mockPost).toHaveBeenCalledWith(`/gamification/xp/${sessionId}`, {
        source: source,
        amount: amount,
        metadata: { description }
      })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getLeaderboard', () => {
    it('should fetch leaderboard data', async () => {
      const mockResponse = {
        data: {
          success: true,
          leaderboard: [
            { username: 'user1', xp: 1000 },
            { username: 'user2', xp: 800 }
          ]
        }
      }

      mockGet.mockResolvedValue(mockResponse)

      const result = await ccmAPI.getLeaderboard('xp', 'weekly')

      expect(mockGet).toHaveBeenCalledWith('/api/v1/gamification/leaderboard?category=xp&period=weekly')
      expect(result).toEqual(mockResponse.data)
    })
  })
})