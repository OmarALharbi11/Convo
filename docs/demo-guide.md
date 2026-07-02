# Demo Guide & Viva Q&A

## Quick Setup

```bash
# Terminal 1 — Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Navigate to `http://localhost:5173/login` and sign in as **Alex Morgan (Manager)**.

---

## Demo Scenarios

### Scenario 1: Email Management (3 minutes)

**Goal:** Demonstrate AI email summarisation, urgency detection, and the read-aloud feature.

1. Navigate to **Email** page
2. Point out the inbox — unread dot indicators, importance stars, relative timestamps
3. Click on the Q3 Budget Review email (high priority)
4. Click **Summarise** → AI summary card appears with urgency badge and key points
5. Click **Read Aloud** → TTS reads the summary
6. Click **Compose** → show the two-step send flow
   - Fill in `to`, `subject`, `body`
   - Click **Review & Send** → confirmation screen shows recipients
   - Say: *"Notice the confirmation step — you can't accidentally send to the wrong person"*
7. Close without sending

**Key talking points:**
- Extractive summarisation without LLM (demonstrates rule-based NLP)
- Two-step confirmation is a safety feature for corporate use
- Urgency detected from keyword matching, not an API call

---

### Scenario 2: Voice Assistant — Read Emails (2 minutes)

**Goal:** Demonstrate full voice pipeline with intent classification.

1. Navigate to **Dashboard**
2. Click the microphone button (large blue button in centre)
3. Say: **"Read my emails"**
4. Point out: transcript appears, intent badge shows `read_emails`
5. The system responds with email count and most urgent message
6. Try text fallback: type "summarise my inbox" in the text field and press Enter
7. Show command history at the bottom

**Key talking points:**
- Rules classifier matches in < 1ms, no LLM needed for common commands
- Confidence score shown in diagnostics (admin view)
- Command history persists during session for repeat actions

---

### Scenario 3: Schedule a Meeting with Confirmation Flow (3 minutes)

**Goal:** Demonstrate the full confirmation flow for high-risk voice actions.

1. On Dashboard, click mic
2. Say: **"Schedule a meeting with Sarah tomorrow at 2pm"**
3. System responds: *"I'd like to schedule a meeting with Sarah on [date] at 14:00. Shall I create this?"*
4. Point out: `requires_confirmation=true`, `action_id` UUID shown
5. Click **Confirm** button (or say "yes")
6. Meeting is created — success toast shown
7. Navigate to Calendar → new event visible
8. Show: clicking Cancel instead — event is NOT created

**Key talking points:**
- UUID token prevents accidental double-confirmation
- 120-second TTL — token expires automatically
- Same pattern for email send and meeting deletion

---

### Scenario 4: RBAC — Role Switching Demo (2 minutes)

**Goal:** Demonstrate server-side role enforcement.

1. Open a second browser tab, navigate to `http://localhost:5173/login`
2. Sign in as **Jamie Lee (Employee)**
3. Notice Audit Log is not in the navigation (hidden for employees)
4. Try navigating to `/audit` manually — "Access Denied" card shown
5. Go to Email → works fine (employees have read_own_email)
6. Try Calendar → employee calendar tab not available (no read_employee_calendar)
7. Switch back to Manager tab — Audit Log visible and working

**Key talking points:**
- RBAC is enforced server-side on every route — frontend hiding is cosmetic only
- Try making an API call directly: `curl -H "Authorization: Bearer <employee_token>" localhost:8000/api/audit/logs` → 403
- Role assigned at login; no client-side privilege escalation possible

---

### Scenario 5: Audit Log (2 minutes) — Manager/Admin only

**Goal:** Demonstrate the security audit trail.

1. As Manager or Admin, navigate to **Audit Log**
2. Show the table: actor email, role, action, resource, outcome, timestamp
3. Filter by action `email.send` — only send actions shown
4. Filter by outcome `denied` — shows any 403 attempts
5. Point out: no email body content in the detail column

**Key talking points:**
- Append-only JSONL file — cannot be modified via API
- IP address and request ID enable forensic analysis
- Employees cannot see the audit log at all

---

## Viva Q&A Preparation

### Architecture

**Q: Why FastAPI instead of Django or Flask?**
FastAPI offers async/await natively, automatic OpenAPI documentation, Pydantic v2 validation, and dependency injection — all of which align well with the async Microsoft Graph calls and the clean dependency tree needed for RBAC. Django would add ORM overhead we don't need since our data lives in Graph, not a database.

**Q: Why did you use an adapter pattern for Graph/STT/TTS?**
The system needed to run in demo mode without Azure credentials for development and evaluation. The adapter pattern lets us swap mock implementations at the factory level — the service layer never needs to know whether it's using real or mock data. This is the same pattern used in production systems for testability.

**Q: How does the intent classifier work?**
The `RulesClassifier` maintains 28 compiled regex patterns across 12 intents. It tries each pattern, extracts named groups as entities, and returns the highest-confidence match. If confidence is below 0.6 AND an OpenAI key is configured, the `LLMIntentParser` is called with a structured prompt asking for JSON output. The `HybridIntentClassifier` takes the higher-confidence result. Rules handle ~85% of commands instantly; LLM handles ambiguous phrasings.

**Q: Why store the Graph token in the JWT?**
For a single-service prototype, this avoids a Redis session store. The trade-off is a larger token and that the Graph token is valid for its own expiry window regardless of IPA logout. Production systems should use a proper session store and token revocation. This is documented in the security notes.

### Security

**Q: How do you prevent an employee from accessing a manager's data?**
Three layers: (1) the `require_permission()` dependency on each route enforces role checks server-side, (2) the `check_resource_access()` function validates cross-user access attempts, (3) the Microsoft Graph API itself enforces the OAuth scopes — the Graph token is scoped to the authenticated user and cannot be used to read another user's mailbox without explicit delegation.

**Q: What happens if the JWT secret is compromised?**
All tokens signed with that secret would need to be considered invalid. The correct response is to rotate the `APP_SECRET_KEY`, which invalidates all existing tokens immediately (users must re-login). In production, short expiry (1-2 hours) combined with refresh tokens limits the blast radius.

**Q: How do you prevent voice commands from sending emails accidentally?**
All `send_email`, `modify_meeting`, and `delete_meeting` intents automatically set `requires_confirmation=True` via the `ClassifiedIntent.model_post_init` method. The voice service stores a pending action with a UUID and 120-second TTL. The action only executes when the user explicitly confirms via the confirmation UI. The confirmation prompt shows the recipient and subject to prevent silent mistakes.

### Design Decisions

**Q: Why not use a proper database for email/calendar data?**
Microsoft Graph is the authoritative store for this data — caching it locally would introduce consistency problems and stale data without adding value. The only locally persisted data is the audit log, which is intentionally kept out of the database as an append-only file to prevent tampering.

**Q: How would this scale to multiple users?**
The current in-memory confirmation store (`_PENDING_ACTIONS` dict) would need to move to Redis. The audit log JSONL would need to move to a proper database. The stateless JWT design means the API tier is already horizontally scalable — each instance just needs the same `APP_SECRET_KEY` and access to the same Redis/database. Microsoft Graph handles the data tier scaling.

**Q: What are the main limitations of the prototype?**
1. Confirmation store is in-memory (single process only)
2. Graph token embedded in JWT (no revocation)
3. Intent entity extraction is rule-based (misses complex phrasings)
4. No real-time notifications (polling only)
5. Calendar conflict detection is client-side only (Graph does server-side validation)

---

## Troubleshooting

| Problem | Solution |
| Backend won't start | Check `APP_SECRET_KEY` is >= 32 chars in `.env` |
| `401 Unauthorized` | JWT expired (8h default) — log out and back in |
| Voice button not working | Allow microphone in browser; check HTTPS context |
| No emails shown | Verify `USE_MOCK_GRAPH=true` in `.env` |
| Tests failing | Ensure `USE_MOCK_GRAPH=true` is set before running pytest |
| CORS errors | Confirm backend is on port 8000, frontend on 5173 |
