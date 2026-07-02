# Risk Register

**Probability:** 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost Certain
**Impact:** 1=Negligible, 2=Minor, 3=Moderate, 4=Major, 5=Critical
**Rating = Probability × Impact**

---

## Technical Risks

| ID | Risk | P | I | Rating | Status | Mitigation |
| T1 | Microsoft Graph API rate limiting (429) interrupts user session | 3 | 3 | 9 | Mitigated | `GraphRateLimitError` caught and surfaced as user-friendly error; retry guidance shown; mock mode bypasses entirely |
| T2 | Azure AD token expiry mid-session causes silent auth failures | 3 | 4 | 12 | Mitigated | IPA JWT expiry (8h) set shorter than Graph token; 401 response triggers frontend redirect to /login |
| T3 | Whisper STT fails on background noise, returning wrong transcript | 4 | 3 | 12 | Accepted | Text fallback input always available; mock mode for demos; confidence < 0.3 triggers clarification request |
| T4 | Intent classifier misidentifies command, performs wrong action | 3 | 4 | 12 | Mitigated | Confirmation flow for all high-risk actions (send_email, delete/modify meeting) prevents irreversible mistakes |
| T5 | Browser denies microphone permission (HTTPS required in production) | 3 | 3 | 9 | Mitigated | Text input fallback on VoicePanel; clear error message with instructions |
| T6 | In-memory confirmation store lost on server restart (pending actions expire) | 2 | 2 | 4 | Accepted | 120s TTL means at most 2-minute user inconvenience; documented as known prototype limitation |
| T7 | SQLite file locking under concurrent requests | 2 | 3 | 6 | Mitigated | SQLAlchemy async engine with connection pool; SQLite WAL mode enabled; PostgreSQL migration path documented |
| T8 | OpenAI API key quota exceeded, disabling LLM intent parsing | 2 | 2 | 4 | Mitigated | Hybrid classifier falls back to rules-only gracefully; feature flag `USE_LLM_INTENT` disables LLM path |
| T9 | Microsoft Graph API breaking change in v1.0 | 1 | 4 | 4 | Accepted | v1.0 is stable/production API; changes are versioned; mock adapter insulates tests from live API changes |
| T10 | Large email body causes STT/TTS context window overflow | 2 | 2 | 4 | Mitigated | Email body truncated to 1000 chars for summarisation; TTS text capped at 500 chars |

---

## Security Risks

| ID | Risk | P | I | Rating | Status | Mitigation |
| S1 | JWT secret brute-forced if weak | 2 | 5 | 10 | Mitigated | Pydantic validator enforces minimum 32-char secret at startup; deployment docs recommend 64-char random value |
| S2 | Graph access token leaked via audit log | 1 | 5 | 5 | Mitigated | `graph_access_token` claim explicitly excluded from all audit log entries; reviewed in code |
| S3 | Employee discovers manager's email via API bypass | 1 | 4 | 4 | Mitigated | Graph token is scoped to the authenticated user only — cannot request another user's mailbox via the same token |
| S4 | XSS in email subject line rendered in UI | 2 | 3 | 6 | Mitigated | React renders all strings as text nodes by default; `dangerouslySetInnerHTML` not used anywhere |
| S5 | CSRF attack submits voice command via malicious page | 1 | 3 | 3 | Mitigated | JWT in `Authorization` header (not cookie); CORS origin whitelist; not exploitable via simple form submission |

---

## Project Risks

| ID | Risk | P | I | Rating | Status | Mitigation |
| P1 | Azure AD tenant registration not available for testing | 3 | 4 | 12 | Mitigated | Full mock mode implemented; all features demonstrable without Azure credentials |
| P2 | Evaluators unfamiliar with voice interface, skewing SUS scores | 3 | 3 | 9 | Mitigated | Demo guide provided; text fallback available; SUS questionnaire includes task-specific items |
| P3 | Scope creep from adding LLM features beyond original spec | 3 | 3 | 9 | Mitigated | LLM intent parsing is optional (feature flag); core system is rule-based to bound scope |
| P4 | Browser compatibility issues with Web Speech API | 2 | 2 | 4 | Accepted | Tested on Chrome 120+; Safari partial support documented; text input fallback ensures usability |
| P5 | Evaluation participants cannot install dev dependencies | 2 | 3 | 6 | Mitigated | Docker Compose enables single-command startup; demo can also run on Replit/Codespaces |

---

## Risk Summary

| Rating Range | Count |
| High (15-25) | 0 |
| Medium (8-14) | 4 |
| Low (1-7) | 11 |

No unmitigated high risks. The four medium risks (T2, T3, T4, P1) are all addressed via the mock mode, confirmation flow, and text fallback strategies.
