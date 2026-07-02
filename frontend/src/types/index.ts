export type UserRole = 'admin' | 'manager' | 'employee'

export interface User {
  user_id: string
  email: string
  display_name: string
  role: UserRole
  permissions: string[]
}

export interface EmailMessage {
  id: string
  subject: string
  sender_name: string
  sender_email: string
  received_at: string
  is_read: boolean
  preview: string
  body_text?: string
  importance: 'high' | 'normal' | 'low'
}

export interface EmailListResponse {
  messages: EmailMessage[]
  total: number
  has_more: boolean
  fetched_at: string
}

export interface EmailSummary {
  message_id: string
  subject: string
  sender_email: string
  key_points: string[]
  sentiment: 'positive' | 'negative' | 'neutral'
  urgency_level: 'high' | 'medium' | 'low'
  summary_text: string
}

export interface SendEmailRequest {
  to: string[]
  subject: string
  body: string
  cc?: string[]
  is_draft?: boolean
}

export interface CalendarEvent {
  event_id: string
  subject: string
  start: string
  end: string
  attendees: string[]
  organizer: string
  location: string
  description: string
  is_online_meeting: boolean
  meeting_url: string
  status: string
}

export interface CalendarEventList {
  events: CalendarEvent[]
  range_start: string
  range_end: string
  total: number
}

export interface AvailabilitySlot {
  start: string
  end: string
  is_available: boolean
  attendees_free: string[]
  attendees_busy: string[]
}

export interface AvailabilityResponse {
  requested_attendees: string[]
  slots: AvailabilitySlot[]
  suggested_times: AvailabilitySlot[]
}

export interface IntentResult {
  intent: string
  entities: Record<string, string>
  confidence: number
  requires_confirmation: boolean
  clarification_needed: boolean
  clarification_question?: string
}

export interface VoiceEntity {
  type: string
  value: string
  raw_text: string
  confidence: number
}

export interface VoiceCommandResponse {
  intent: string
  confidence: number
  transcript: string
  response_text: string
  action_result?: Record<string, unknown>
  tts_audio_base64?: string
  requires_confirmation: boolean
  action_id?: string
  clarification_needed: boolean
  clarification_question?: string
  entities?: VoiceEntity[]
}

export interface AuditEntry {
  id: string
  actor_id: string
  actor_email: string
  actor_role: string
  action: string
  target_resource: string
  outcome: 'success' | 'failure' | 'denied'
  detail: Record<string, unknown>
  request_id: string
  ip_address: string
  timestamp: string
}

export interface AuditLogResponse {
  entries: AuditEntry[]
  total: number
}

export type VoiceState =
  | 'idle'
  | 'recording'
  | 'processing'
  | 'responding'
  | 'confirming'
  | 'error'

export interface CommandHistoryEntry {
  id: string
  transcript: string
  intent: string
  response_text: string
  timestamp: Date
  success: boolean
  requires_confirmation?: boolean
}
