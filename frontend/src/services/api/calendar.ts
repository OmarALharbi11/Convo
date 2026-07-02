import { apiClient } from './client'
import type { AvailabilityResponse, CalendarEvent, CalendarEventList } from '@/types'

interface CreateEventRequest {
  subject: string
  start: string
  end: string
  attendees?: string[]
  location?: string
  description?: string
  is_online_meeting?: boolean
}

interface UpdateEventRequest {
  subject?: string
  start?: string
  end?: string
  attendees?: string[]
  location?: string
}

interface AvailabilityRequest {
  attendee_emails: string[]
  start: string
  end: string
  duration_minutes?: number
}

export const calendarApi = {
  getToday: (): Promise<CalendarEventList> =>
    apiClient.get('/api/calendar/today'),

  getWeek: (): Promise<CalendarEventList> =>
    apiClient.get('/api/calendar/week'),

  getEvents: (start?: string, end?: string): Promise<CalendarEventList> =>
    apiClient.get('/api/calendar/events', { start, end }),

  getEmployeeCalendar: (email: string, start?: string, end?: string): Promise<CalendarEventList> =>
    apiClient.get(`/api/calendar/employee/${encodeURIComponent(email)}/events`, { start, end }),

  createEvent: (data: CreateEventRequest): Promise<CalendarEvent> =>
    apiClient.post('/api/calendar/events', data),

  updateEvent: (id: string, data: UpdateEventRequest): Promise<CalendarEvent> =>
    apiClient.patch(`/api/calendar/events/${id}`, data),

  deleteEvent: (id: string): Promise<void> =>
    apiClient.delete(`/api/calendar/events/${id}`),

  checkAvailability: (data: AvailabilityRequest): Promise<AvailabilityResponse> =>
    apiClient.post('/api/calendar/availability', data),
}
