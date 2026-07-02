import { apiClient } from './client'
import type { EmailListResponse, EmailMessage, EmailSummary, SendEmailRequest } from '@/types'

interface SendEmailResponse {
  message_id: string
  status: string
  sent_at: string
}

export const emailApi = {
  getInbox: (params?: { limit?: number; only_unread?: boolean; folder?: string }): Promise<EmailListResponse> =>
    apiClient.get('/api/email/inbox', params),

  getMessage: (id: string): Promise<EmailMessage> =>
    apiClient.get(`/api/email/messages/${id}`),

  summariseMessage: (id: string): Promise<EmailSummary> =>
    apiClient.get(`/api/email/messages/${id}/summary`),

  getSummaries: (count = 5): Promise<EmailSummary[]> =>
    apiClient.get('/api/email/summary/recent', { count }),

  sendEmail: (data: SendEmailRequest): Promise<SendEmailResponse> =>
    apiClient.post('/api/email/send', data),

  createDraft: (data: SendEmailRequest): Promise<SendEmailResponse> =>
    apiClient.post('/api/email/draft', data),
}
