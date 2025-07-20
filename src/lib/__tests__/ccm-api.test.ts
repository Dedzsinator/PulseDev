import { describe, it, expect, beforeEach, vi } from 'vitest'
import { 
  submitContextEvent, 
  getGamificationDashboard,
  awardXP,
  getLeaderboard 
} from '../ccm-api'
import { api } from '../api'

vi.mock('../api')
const mockedApi = vi.mocked(api)

describe('CCM API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('submitContextEvent', () => {
    it('should submit context event successfully', async () => {
      const mockEvent = {
        sessionId: 'test-session',
        agent: 'vscode',
        type: 'file_edit',
        payload: { file: 'test.ts' },
        timestamp: new Date().toISOString()
      }

      const mockResponse = { data: { status: 'success', event_id: '123' } }
      mockedApi.post.mockResolvedValue(mockResponse)

      const result = await submitContextEvent(mockEvent)

      expect(mockedApi.post).toHaveBeenCalledWith('/api/v1/context/events', mockEvent)
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

      mockedApi.post.mockRejectedValue(new Error('API Error'))

      await expect(submitContextEvent(mockEvent)).rejects.toThrow('API Error')
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

      mockedApi.get.mockResolvedValue(mockResponse)

      const result = await getGamificationDashboard(sessionId)

      expect(mockedApi.get).toHaveBeenCalledWith(`/api/v1/gamification/dashboard/${sessionId}`)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('awardXP', () => {
    it('should award XP successfully', async () => {
      const request = {
        session_id: 'test-session',
        source: 'commit',
        amount: 100,
        description: 'Test commit'
      }

      const mockResponse = {
        data: { success: true, xp_earned: 100 }
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const result = await awardXP(request)

      expect(mockedApi.post).toHaveBeenCalledWith('/api/v1/gamification/xp/award', request)
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

      mockedApi.get.mockResolvedValue(mockResponse)

      const result = await getLeaderboard('xp', 'weekly')

      expect(mockedApi.get).toHaveBeenCalledWith('/api/v1/gamification/leaderboard?category=xp&period=weekly')
      expect(result).toEqual(mockResponse.data)
    })
  })
})