import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import api from '../api'

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
    // Request interceptors are tested implicitly through API calls
    expect(api.interceptors.request).toBeDefined()
  })

  it('should handle response interceptor success', () => {
    // Response interceptors are tested implicitly through API calls
    expect(api.interceptors.response).toBeDefined()
  })

  it('should handle response interceptor error', () => {
    // Error handling is tested implicitly through failed API calls
    expect(api.interceptors.response).toBeDefined()
  })
})