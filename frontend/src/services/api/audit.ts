import { apiClient } from './client'
import type { AuditLogResponse } from '@/types'

interface AuditLogParams {
  [key: string]: string | number | boolean | undefined
  limit?: number
  offset?: number
  action_filter?: string
  actor_filter?: string
  since?: string
  until?: string
}

export const auditApi = {
  getLogs: (params?: AuditLogParams): Promise<AuditLogResponse> =>
    apiClient.get('/api/audit/logs', params),

  getMyLogs: (limit = 20): Promise<AuditLogResponse> =>
    apiClient.get('/api/audit/logs/my', { limit }),
}
