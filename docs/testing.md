# Testing Strategy

## Overview

The test suite uses `pytest-asyncio` with `httpx.AsyncClient` and FastAPI's `ASGITransport` for in-process integration tests. All tests run in mock mode (`USE_MOCK_GRAPH=true`, `USE_MOCK_STT=true`, `USE_MOCK_TTS=true`) — no external services required.

---

## Test Categories

### 1. RBAC Unit Tests (`test_rbac.py`)

Tests the permission matrix in isolation, without HTTP.

| Test | Description |
| `test_employee_read_own_email` | Employee has `read_own_email` |
| `test_employee_cannot_read_employee_calendar` | Employee lacks `read_employee_calendar` |
| `test_employee_cannot_view_audit` | Employee lacks `view_audit_log` |
| `test_manager_read_employee_calendar` | Manager has `read_employee_calendar` |
| `test_manager_view_audit` | Manager has `view_audit_log` |
| `test_manager_cannot_manage_users` | Manager lacks `manage_users` |
| `test_admin_has_all_permissions` | Admin has every permission |
| `test_check_resource_own_access` | User can access own resource |
| `test_check_resource_cross_user_denied` | Employee blocked from another's resource |
| `test_check_resource_manager_cross_user` | Manager allowed cross-user with permission |
| `test_require_permission_allows` | Dependency returns user when permitted |
| `test_require_permission_denies_403` | Dependency raises HTTP 403 when denied |
| `test_role_hierarchy_ordering` | Admin > Manager > Employee ordering |

**Route protection integration:**

| Route | Role | Expected |
| `GET /api/email/inbox` | anonymous | 401 |
| `GET /api/email/inbox` | employee | 200 |
| `GET /api/calendar/employee/other` | employee | 403 |
| `GET /api/calendar/employee/other` | manager | 200 |
| `GET /api/audit/logs` | employee | 403 |
| `GET /api/audit/logs` | manager | 200 |
| `GET /api/admin/diagnostics` | manager | 403 |
| `GET /api/admin/diagnostics` | admin | 200 |

---

### 2. Intent Engine Tests (`test_intent_engine.py`)

Tests `RulesClassifier` and `HybridIntentClassifier` directly.

**Intent recognition:**

| Input | Expected Intent |
| "read my emails" | `read_emails` |
| "show unread messages" | `read_emails` |
| "summarise my inbox" | `summarise_emails` |
| "send an email to John" | `send_email` |
| "what's on my calendar today" | `list_calendar_events` |
| "schedule a meeting with Sarah tomorrow at 2pm" | `create_meeting` |
| "cancel my 3pm meeting" | `delete_meeting` |
| "check availability for Alice and Bob" | `check_availability` |
| "read notifications" | `read_notifications` |
| "help" | `help` |
| "qwerty blargh" | `unknown` |

**Entity extraction:**

| Input | Expected entities |
| "email Sarah about the project" | `{person: "Sarah", email_subject: "the project"}` |
| "meeting tomorrow at 2pm" | `{date: "<tomorrow's date>", time: "14:00"}` |
| "meeting for 30 minutes" | `{duration: "30 minutes"}` |
| "in the boardroom" | `{location: "the boardroom"}` |

**Confidence thresholds:**

| Scenario | Expected |
| Clear intent match | confidence ≥ 0.8 |
| Vague phrase | confidence < 0.6 |
| Unknown input | intent = `unknown`, clarification_needed = True |

**Confirmation flags:**

| Intent | requires_confirmation |
| `send_email` | True |
| `modify_meeting` | True |
| `delete_meeting` | True |
| `read_emails` | False |
| `list_calendar_events` | False |

---

### 3. Email API Tests (`test_email.py`)

| Test | Description |
| `test_inbox_returns_messages` | 200, messages list non-empty |
| `test_inbox_unread_filter` | `only_unread=true` returns subset |
| `test_inbox_limit` | `limit=2` returns max 2 messages |
| `test_message_by_id` | GET by ID returns body_text |
| `test_message_not_found` | Unknown ID returns 404 |
| `test_summaries` | Returns key_points, urgency_level |
| `test_send_email_success` | POST /send returns `status: sent` |
| `test_send_email_empty_to` | 422 validation error |
| `test_send_email_empty_body` | 422 validation error |
| `test_employee_can_send` | Employee role can send |
| `test_anonymous_401` | No JWT → 401 |

---

### 4. Calendar API Tests (`test_calendar.py`)

| Test | Description |
| `test_today_returns_events` | Events list with correct fields |
| `test_week_returns_events` | Week view non-empty |
| `test_event_has_required_fields` | event_id, subject, start, end present |
| `test_create_event` | POST returns 201, new event_id |
| `test_create_event_end_before_start` | 422 validation error |
| `test_update_event` | PATCH updates subject |
| `test_delete_event` | DELETE returns `{"deleted": true}` |
| `test_employee_blocked_from_employee_calendar` | 403 |
| `test_manager_can_read_employee_calendar` | 200 |
| `test_availability_check` | Returns suggested_times list |

---

### 5. Voice Pipeline Tests (`test_voice.py`)

| Test | Description |
| `test_transcribe_audio` | Returns transcript string |
| `test_command_read_emails` | Intent = read_emails, response_text present |
| `test_command_send_email_requires_confirmation` | requires_confirmation=True, action_id returned |
| `test_confirm_action_executes` | `confirmed=true` → executed=True |
| `test_cancel_action` | `confirmed=false` → executed=False |
| `test_unknown_command_clarification` | clarification_needed=True for gibberish |
| `test_tts_returns_audio` | audio_base64 or empty bytes |
| `test_empty_transcript_422` | Empty text → 422 |
| `test_intent_diagnostics_admin_only` | Employee 403, admin 200 |
| `test_command_create_meeting` | Intent = create_meeting, confirmation required |

---

### 6. Auth Tests (`test_auth.py`)

| Test | Description |
| `test_mock_login_manager` | Returns JWT, role=manager |
| `test_mock_login_admin` | Returns JWT, role=admin |
| `test_mock_login_employee` | Returns JWT, role=employee |
| `test_me_endpoint` | Returns user_id, email, permissions list |
| `test_permissions_employee` | Does not include view_audit_log |
| `test_permissions_manager` | Includes view_audit_log |
| `test_invalid_token_401` | Malformed JWT → 401 |
| `test_expired_token_401` | Expired JWT → 401 |

---

### 7. Audit Log Tests (`test_audit.py`)

| Test | Description |
| `test_my_logs_accessible_to_all` | Any role can call /logs/my |
| `test_employee_blocked_from_all_logs` | Employee → 403 |
| `test_manager_sees_all_logs` | Manager → 200, entries list |
| `test_email_read_creates_audit_entry` | Read inbox → audit entry written |
| `test_audit_entry_structure` | id, actor_email, action, outcome present |
| `test_no_body_in_audit` | Email body not in detail dict |
| `test_action_filter` | `action_filter=email.send` filters correctly |
| `test_permission_denied_logged` | 403 response → denied entry in audit |

---

## Running Tests

```bash
cd backend

# All tests
pytest -v

# Specific file
pytest tests/test_intent_engine.py -v

# With coverage
pytest --cov=app --cov-report=html

# Only fast unit tests
pytest tests/test_rbac.py tests/test_intent_engine.py -v
```

---

## Coverage Goals

| Module | Target |
| `app/core/rbac.py` | 100% |
| `app/intents/` | ≥ 90% |
| `app/api/routes/` | ≥ 85% |
| `app/services/` | ≥ 80% |
| `app/integrations/` | ≥ 75% (mock path) |

---

## Test Data

Mock data used across all tests (defined in `conftest.py` and `mock_adapter.py`):

- **8 mock emails** from Contoso Corp (varying urgency/read status)
- **6 mock calendar events** (today + next 4 days)
- **3 test JWT fixtures**: manager_token, employee_token, admin_token
- **4 test HTTP clients**: manager_client, employee_client, admin_client, anon_client
