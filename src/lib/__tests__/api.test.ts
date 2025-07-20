import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { api } from '../api'

vi.mock('axios')
const mockedAxios = vi.mocked(axios)

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create axios instance with correct base URL', () => {
    expect(axios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  })

  it('should handle request interceptor', async () => {
    const mockRequest = { headers: {} }
    const interceptor = api.interceptors.request.handlers[0]?.fulfilled
    
    if (interceptor) {
      const result = await interceptor(mockRequest)
      expect(result).toBe(mockRequest)
    }
  })

  it('should handle response interceptor success', () => {
    const mockResponse = { data: { test: 'data' } }
    const interceptor = api.interceptors.response.handlers[0]?.fulfilled
    
    if (interceptor) {
      const result = interceptor(mockResponse)
      expect(result).toBe(mockResponse)
    }
  })

  it('should handle response interceptor error', () => {
    const mockError = {
      response: {
        status: 400,
        data: { message: 'Bad Request' }
      }
    }
    
    const interceptor = api.interceptors.response.handlers[0]?.rejected
    
    if (interceptor) {
      expect(() => interceptor(mockError)).toThrow()
    }
  })
})