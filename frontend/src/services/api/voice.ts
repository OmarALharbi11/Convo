import { apiClient } from './client'
import type { VoiceCommandResponse } from '@/types'

interface TranscriptionResponse {
  transcript: string
  confidence: number
  language: string
}

interface TTSResponse {
  audio_data: string
  mime_type: string
  duration_seconds: number
}

export const voiceApi = {
  transcribe: (audioBase64: string, mimeType = 'audio/webm'): Promise<TranscriptionResponse> =>
    apiClient.post('/api/voice/transcribe', {
      audio_data: audioBase64,
      language: 'en-US',
      mime_type: mimeType,
    }),

  processCommand: (transcript: string): Promise<VoiceCommandResponse> =>
    apiClient.post('/api/voice/command', { transcript }),

  confirmAction: (actionId: string, confirmed: boolean): Promise<VoiceCommandResponse> =>
    apiClient.post('/api/voice/confirm', { action_id: actionId, confirmed }),

  textToSpeech: (text: string): Promise<TTSResponse> =>
    apiClient.post('/api/voice/tts', { text }),

  getIntentDiagnostics: (): Promise<Record<string, unknown>> =>
    apiClient.get('/api/voice/intent-diagnostics'),
}
