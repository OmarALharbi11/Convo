# Requirements Specification

## Functional Requirements

### Authentication & Authorisation

| ID | Requirement | Priority |
| FR-1 | The system shall authenticate users via Microsoft OAuth 2.0 (delegated flow) | Must |
| FR-2 | The system shall support a demo/mock login mode without Azure credentials | Must |
| FR-3 | The system shall enforce RBAC with three roles: Admin, Manager, Employee | Must |
| FR-4 | The system shall embed user role and Graph token in a signed JWT | Must |
| FR-5 | The system shall return HTTP 403 with a clear message for permission violations | Must |

### Email Management

| ID | Requirement | Priority |
| FR-6 | The system shall fetch the user's inbox from Microsoft Graph (Mail.Read scope) | Must |
| FR-7 | The system shall display sender, subject, timestamp, read status, and importance | Must |
| FR-8 | The system shall generate an AI summary of an individual email message | Must |
| FR-9 | The system shall generate summaries for the N most recent emails | Should |
| FR-10 | The system shall send emails via Microsoft Graph (Mail.Send scope) with a confirmation step | Must |
| FR-11 | The system shall support CC recipients and email drafts | Should |
| FR-12 | Summaries shall include urgency level (high/medium/low), sentiment, and key points | Must |

### Calendar Management

| ID | Requirement | Priority |
| FR-13 | The system shall display today's and this week's calendar events | Must |
| FR-14 | The system shall show event subject, time, duration, location, attendees, and online meeting link | Must |
| FR-15 | The system shall allow creating new calendar events with attendees | Must |
| FR-16 | The system shall allow updating and deleting existing events with confirmation | Must |
| FR-17 | Managers shall be able to view employee availability (free/busy slots) | Must |
| FR-18 | The system shall suggest available time slots given attendees and desired duration | Should |

### Voice Assistant

| ID | Requirement | Priority |
| FR-19 | The system shall capture microphone audio via the browser (MediaRecorder API) | Must |
| FR-20 | The system shall transcribe audio using Whisper STT (or mock provider) | Must |
| FR-21 | The system shall classify voice commands into 12 supported intents | Must |
| FR-22 | The system shall extract entities (person, date, time, location, subject) from commands | Must |
| FR-23 | The system shall execute email and calendar actions in response to classified intents | Must |
| FR-24 | High-risk actions (send_email, modify/delete meeting) shall require explicit confirmation | Must |
| FR-25 | The system shall respond with natural language text and optional TTS audio | Must |
| FR-26 | The system shall provide a text fallback input when voice is unavailable | Must |
| FR-27 | The system shall maintain a command history for the session | Should |
| FR-28 | If the intent classifier is unsure, the system shall request clarification | Should |

### Audit Logging

| ID | Requirement | Priority |
| FR-29 | The system shall log every security-relevant action to an append-only JSONL file | Must |
| FR-30 | Audit entries shall include actor identity, action, target, outcome, and timestamp | Must |
| FR-31 | Email body content shall never appear in audit log entries | Must |
| FR-32 | Managers and admins shall be able to query audit logs with filters | Must |
| FR-33 | All users shall be able to view their own audit entries | Should |

---

## Non-Functional Requirements

| ID | Requirement | Category | Measure |
| NFR-1 | Voice command pipeline end-to-end latency < 3 seconds (mock mode) | Performance | ≤ 3s p95 |
| NFR-2 | API responses for email/calendar < 500ms (mock mode) | Performance | ≤ 500ms p95 |
| NFR-3 | Intent classification (rules only) < 5ms | Performance | ≤ 5ms |
| NFR-4 | System shall run without Azure credentials in mock mode | Availability | 100% of features in mock mode |
| NFR-5 | All API endpoints shall validate inputs and return structured error messages | Reliability | 0 unhandled exceptions |
| NFR-6 | JWT tokens shall expire within 8 hours | Security | ≤ 8h |
| NFR-7 | Signing secret shall be at least 32 characters | Security | Enforced at startup |
| NFR-8 | System shall achieve SUS score ≥ 70 in evaluation | Usability | SUS ≥ 70 |
| NFR-9 | The system shall be operable without audio hardware (text fallback) | Accessibility | All features accessible via keyboard |
| NFR-10 | Frontend shall render correctly in Chrome 120+, Firefox 120+, Edge 120+ | Compatibility | Tested browsers |
| NFR-11 | Codebase shall have ≥ 80% test coverage on core business logic | Maintainability | pytest-cov ≥ 80% |
| NFR-12 | Docker Compose startup shall complete within 60 seconds | Deployability | ≤ 60s from cold start |

---

## Use Cases

### UC-1: Read Email Summary (Primary)
- **Actor:** Manager
- **Precondition:** User is authenticated
- **Main flow:** User issues "summarise my inbox" voice command → system classifies intent → fetches top 5 emails → generates summaries → reads aloud
- **Alternative:** User clicks Summarise button on a specific email
- **Exception:** Graph API unavailable → mock adapter used, error surfaced to user

### UC-2: Schedule Meeting (Primary)
- **Actor:** Manager
- **Precondition:** User is authenticated with write_own_calendar permission
- **Main flow:** User says "schedule meeting with Sarah tomorrow at 2pm" → intent classified as create_meeting → entities extracted → confirmation prompt shown → user confirms → event created in Graph
- **Exception:** Conflict detected → user notified, prompted to choose different time

### UC-3: View Employee Calendar (Secondary)
- **Actor:** Manager
- **Precondition:** User has read_employee_calendar permission
- **Main flow:** Manager requests availability check for attendees → system calls Graph scheduleInformation → free/busy slots calculated → suggested times returned
- **Exception:** Employee has no Graph account → graceful error, mock data used

### UC-4: Review Audit Log (Tertiary)
- **Actor:** Admin or Manager
- **Precondition:** User has view_audit_log permission
- **Main flow:** User navigates to Audit Log → applies filters (action type, date range) → table displays matching entries
- **Exception:** No matching entries → empty state shown

---

## Requirements Traceability Matrix

| Requirement | Implemented In | Test Coverage |
| FR-1, FR-2 | `app/api/routes/auth.py` | `test_auth.py` |
| FR-3, FR-4, FR-5 | `app/core/rbac.py`, `app/core/security.py` | `test_rbac.py` |
| FR-6 – FR-12 | `app/services/email_service.py`, `app/api/routes/email.py` | `test_email.py` |
| FR-13 – FR-18 | `app/services/calendar_service.py`, `app/api/routes/calendar.py` | `test_calendar.py` |
| FR-19 – FR-28 | `app/services/voice_service.py`, `app/api/routes/voice.py`, `app/intents/` | `test_voice.py`, `test_intent_engine.py` |
| FR-29 – FR-33 | `app/core/audit_logger.py`, `app/api/routes/audit.py` | `test_audit.py` |
| NFR-1 – NFR-3 | Mock adapters, sync rules classifier | Performance assertions in `test_voice.py` |
| NFR-5 | FastAPI exception handlers in `app/main.py` | All route tests |
| NFR-6, NFR-7 | `app/core/config.py`, `app/core/security.py` | `test_auth.py` |
