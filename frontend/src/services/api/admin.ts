import { apiClient } from './client'

interface DiagnosticsResponse {
  environment?: string
  version?: string
  uptime?: string
  mock_mode?: { graph?: boolean; stt?: boolean; tts?: boolean }
  llm_intent_enabled?: boolean
  last_intent_debug?: Record<string, unknown>
  audit_stats?: { total?: number; success?: number; denied?: number }
}

export const adminApi = {
  getDiagnostics: (): Promise<DiagnosticsResponse> =>
    apiClient.get('/api/admin/diagnostics'),
}
