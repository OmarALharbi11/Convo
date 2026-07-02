# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

All authenticated endpoints require: `Authorization: Bearer <jwt_token>`

---

## Authentication

### GET /api/auth/login
Initiates Microsoft OAuth 2.0 flow.

**Response 200:**
```json
{ "auth_url": "https://login.microsoftonline.com/..." }
```

---

### GET /api/auth/callback
Completes OAuth flow after redirect from Microsoft.

**Query params:** `code`, `state`

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

---

### POST /api/auth/mock-login
**Dev/demo only.** Issues a JWT without Azure credentials.

**Request:**
```json
{ "role": "manager", "name": "Alex Morgan" }
```

**Response 200:** Same as `/callback`.

---

### GET /api/auth/me
Returns the current user's profile and permissions.

**Response 200:**
```json
{
  "user_id": "mock-manager-001",
  "email": "alex.morgan@contoso.com",
  "display_name": "Alex Morgan",
  "role": "manager",
  "permissions": ["read_own_email", "send_email", "read_own_calendar", ...]
}
```

---

### GET /api/auth/status
Returns auth configuration status (unauthenticated).

**Response 200:**
```json
{ "mock_mode": true, "environment": "development" }
```

---

### POST /api/auth/logout
Invalidates session (clears server-side token reference).

**Response 200:** `{ "message": "Logged out successfully." }`

---

## Email

All email endpoints require `read_own_email` permission.

### GET /api/email/inbox
Fetch inbox messages.

**Query params:**
- `limit` (int, default 20) — number of messages
- `only_unread` (bool, default false) — filter to unread only

**Response 200:**
```json
{
  "messages": [
    {
      "id": "msg-001",
      "subject": "Q3 Budget Review",
      "sender_name": "Sarah Chen",
      "sender_email": "s.chen@contoso.com",
      "received_at": "2024-03-15T09:00:00Z",
      "is_read": false,
      "preview": "Please review the attached budget...",
      "importance": "high"
    }
  ],
  "total": 8,
  "has_more": false,
  "fetched_at": "2024-03-15T10:00:00Z"
}
```

---

### GET /api/email/messages/{message_id}
Fetch a specific message including body text.

**Response 200:** `EmailMessage` with `body_text` field populated.

---

### GET /api/email/messages/{message_id}/summary
AI-generated summary of a message.

**Response 200:**
```json
{
  "message_id": "msg-001",
  "subject": "Q3 Budget Review",
  "sender_email": "s.chen@contoso.com",
  "key_points": ["Budget shortfall of 12%", "Meeting requested by Friday"],
  "sentiment": "neutral",
  "urgency_level": "high",
  "summary_text": "Sarah Chen requests an urgent review of Q3 budget..."
}
```

---

### GET /api/email/summaries
Summaries of the most recent N messages.

**Query params:** `limit` (default 5)

**Response 200:** `{ "summaries": [...] }`

---

### POST /api/email/send
Send an email. Requires `send_email` permission.

**Request:**
```json
{
  "to": ["recipient@contoso.com"],
  "subject": "Meeting follow-up",
  "body": "As discussed...",
  "cc": []
}
```

**Response 200:**
```json
{ "message_id": "sent-xxx", "status": "sent" }
```

---

### POST /api/email/draft
Save as draft. Requires `send_email` permission.

**Request:** Same as `/send`.

**Response 200:** `{ "draft_id": "draft-xxx", "status": "saved" }`

---

## Calendar

### GET /api/calendar/today
Events for today.

**Response 200:**
```json
{
  "events": [
    {
      "event_id": "evt-001",
      "subject": "Daily Standup",
      "start": "2024-03-15T09:30:00Z",
      "end": "2024-03-15T09:45:00Z",
      "attendees": ["alice@contoso.com", "bob@contoso.com"],
      "organizer": "alex.morgan@contoso.com",
      "location": "Teams",
      "description": "",
      "is_online_meeting": true,
      "meeting_url": "https://teams.microsoft.com/...",
      "status": "accepted"
    }
  ],
  "range_start": "2024-03-15T00:00:00Z",
  "range_end": "2024-03-15T23:59:59Z",
  "total": 3
}
```

---

### GET /api/calendar/week
Events for the current week.

**Response 200:** Same structure as `/today`.

---

### GET /api/calendar/events
Events for a date range.

**Query params:** `start` (ISO), `end` (ISO)

---

### GET /api/calendar/employee/{user_id}
View another user's calendar. Requires `read_employee_calendar` permission (manager+).

---

### POST /api/calendar/events
Create a new calendar event. Requires `write_own_calendar` permission.

**Request:**
```json
{
  "subject": "Budget Review",
  "start": "2024-03-20T14:00:00Z",
  "end": "2024-03-20T15:00:00Z",
  "attendees": ["sarah@contoso.com"],
  "location": "Conference Room B",
  "is_online_meeting": false
}
```

**Response 201:** Created `CalendarEvent` object.

---

### PATCH /api/calendar/events/{event_id}
Update a calendar event. Requires `write_own_calendar` permission.

**Request:** Partial `CalendarEvent` fields.

---

### DELETE /api/calendar/events/{event_id}
Delete a calendar event. Requires `write_own_calendar` permission.

**Response 200:** `{ "deleted": true }`

---

### POST /api/calendar/availability
Check attendee availability. Requires `read_employee_calendar` permission.

**Request:**
```json
{
  "attendees": ["alice@contoso.com", "bob@contoso.com"],
  "start": "2024-03-20T09:00:00Z",
  "end": "2024-03-20T17:00:00Z",
  "duration_minutes": 60
}
```

**Response 200:**
```json
{
  "requested_attendees": ["alice@contoso.com", "bob@contoso.com"],
  "slots": [...],
  "suggested_times": [
    {
      "start": "2024-03-20T10:00:00Z",
      "end": "2024-03-20T11:00:00Z",
      "is_available": true,
      "attendees_free": ["alice@contoso.com", "bob@contoso.com"],
      "attendees_busy": []
    }
  ]
}
```

---

## Voice

### POST /api/voice/transcribe
Transcribe audio to text.

**Request:** `multipart/form-data` with `audio` file field.

**Response 200:**
```json
{ "transcript": "Read my emails", "confidence": 0.95 }
```

---

### POST /api/voice/command
Process a voice command text.

**Request:**
```json
{ "text": "Schedule a meeting with Sarah tomorrow at 2pm" }
```

**Response 200:**
```json
{
  "intent": "create_meeting",
  "confidence": 0.92,
  "transcript": "Schedule a meeting with Sarah tomorrow at 2pm",
  "response_text": "I'd like to schedule a meeting with Sarah on 2024-03-16 at 14:00. Shall I create this?",
  "action_result": null,
  "tts_audio_base64": null,
  "requires_confirmation": true,
  "action_id": "a1b2c3d4-...",
  "clarification_needed": false,
  "clarification_question": null
}
```

---

### POST /api/voice/confirm
Confirm or cancel a pending action.

**Request:**
```json
{ "action_id": "a1b2c3d4-...", "confirmed": true }
```

**Response 200:**
```json
{
  "executed": true,
  "response_text": "Meeting scheduled successfully.",
  "action_result": { "event_id": "evt-new-123" }
}
```

---

### POST /api/voice/tts
Convert text to speech audio.

**Request:**
```json
{ "text": "You have 3 unread emails." }
```

**Response 200:**
```json
{ "audio_base64": "UklGRi...", "format": "wav" }
```

---

### GET /api/voice/intent-diagnostics
Returns debug info about the last classification. Admin only.

---

## Audit

### GET /api/audit/logs
All audit log entries. Requires `view_audit_log` permission (manager+).

**Query params:**
- `limit` (default 50)
- `offset` (default 0)
- `action_filter` (string, e.g. `email.send`)
- `actor_filter` (user email)
- `since` / `until` (ISO timestamps)

**Response 200:**
```json
{
  "entries": [
    {
      "id": "uuid",
      "actor_id": "user-001",
      "actor_email": "alex@contoso.com",
      "actor_role": "manager",
      "action": "email.send",
      "target_resource": "msg-sent-001",
      "outcome": "success",
      "detail": { "subject": "Q3 Follow-up", "recipient_count": 1 },
      "request_id": "req-uuid",
      "ip_address": "127.0.0.1",
      "timestamp": "2024-03-15T10:05:00Z"
    }
  ],
  "total": 142
}
```

---

### GET /api/audit/logs/my
The current user's own audit entries. Any authenticated user.

**Query params:** `limit` (default 20)

---

## Admin

### GET /api/admin/diagnostics
System diagnostics. Requires `access_diagnostics` permission (admin only).

**Response 200:**
```json
{
  "environment": "development",
  "version": "1.0.0",
  "uptime": "2h 34m",
  "mock_mode": { "graph": true, "stt": true, "tts": true },
  "llm_intent_enabled": false,
  "last_intent_debug": { ... },
  "audit_stats": { "total": 142, "success": 138, "denied": 4 }
}
```

---

## Health

### GET /api/health
Returns service health (unauthenticated).

**Response 200:**
```json
{ "status": "ok", "version": "1.0.0", "timestamp": "..." }
```

---

## Error Responses

All errors follow this structure:

```json
{
  "detail": "Human-readable message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid JWT |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g. scheduling overlap) |
| 422 | Request body validation failed (includes field details) |
| 429 | Microsoft Graph rate limit hit |
| 500 | Internal server error |
