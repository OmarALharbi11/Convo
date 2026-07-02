import { apiClient } from './client'
import type { User } from '@/types'

interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

interface MockLoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export const authApi = {
  mockLogin: (role: string, name: string): Promise<MockLoginResponse> =>
    apiClient.post('/api/auth/mock-login', { role, name }),

  getLoginUrl: (): Promise<{ auth_url: string }> =>
    apiClient.get('/api/auth/login'),

  callback: (code: string, state?: string): Promise<TokenResponse> =>
    apiClient.get(`/api/auth/callback?code=${encodeURIComponent(code)}${state ? `&state=${encodeURIComponent(state)}` : ''}`),

  getMe: (): Promise<User> =>
    apiClient.get('/api/auth/me'),

  logout: (): Promise<void> =>
    apiClient.post('/api/auth/logout'),

  getStatus: (): Promise<Record<string, unknown>> =>
    apiClient.get('/api/auth/status'),
}
