# Convo — Voice Assistant for Corporate Managers

Convo is a browser-based voice assistant I built as my final-year computing project. The idea was simple: corporate managers spend a lot of time triaging emails and chasing calendar slots — Convo lets them do all of that by just speaking naturally.

You can say things like *"Schedule a meeting with Sarah tomorrow at 2 PM"* or *"Summarise my unread emails"* and Convo figures out what you mean, asks for confirmation where it matters, and gets it done. It runs entirely in demo mode out of the box — no Azure account or API keys needed to try it.

---

## What it does

- **Voice and text commands** — speak or type; Convo understands natural language using a hybrid classifier (regex rules + optional GPT-4o-mini fallback for edge cases)
- **Email** — read your inbox, view messages, get AI-generated summaries, compose and send with a confirmation step
- **Calendar** — see today's schedule or the full week, create, update and delete meetings, check team availability
- **Manager team view** — managers can pull up any team member's calendar; employees can only see their own
- **Role-based access control** — three roles (Employee, Manager, Admin) with a strict permission matrix enforced on every API route
- **Confirmation flow** — anything risky (sending an email, deleting a meeting) gets staged first and waits for you to say yes
- **Audit trail** — every sensitive action is written to an append-only log; email bodies and voice transcripts are never stored

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend framework | FastAPI + Uvicorn | 0.111 / 0.29 |
| Data validation | Pydantic v2 | 2.7.1 |
| Auth | MSAL + python-jose (JWT HS256) | 1.28 / 3.3 |
| Password hashing | passlib bcrypt | 1.7.4 |
| HTTP client | httpx | 0.27 |
| Database (ORM) | SQLAlchemy + aiosqlite | 2.0.30 |
| Migrations | Alembic | 1.13.1 |
| Graph API | Microsoft Graph REST v1.0 | — |
| STT | Browser Web Speech API / OpenAI Whisper | — |
| TTS | Browser `speechSynthesis` / OpenAI tts-1 | — |
| Logging | structlog | 24.1 |
| Frontend framework | React 18 + TypeScript + Vite | 18.3 / 5.4 / 5.2 |
| Server state | TanStack Query v5 | 5.40 |
| Client state | Zustand v4 | 4.5 |
| Styling | Tailwind CSS v3 | 3.4 |
| Router | React Router v6 | 6.23 |
| Icons | Lucide React | 0.379 |

---

## Getting started

### What you need

- Python 3.11+
- Node.js 18+
- Chrome or Edge (for the microphone / Web Speech API)
- Azure AD app registration *(optional — only needed for live Microsoft 365 data)*
- OpenAI API key *(optional — only needed for Whisper STT and tts-1 voice output)*

### 1. Start the backend

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` and the interactive docs are at `http://localhost:8000/docs`.

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app opens at `http://localhost:5173`.

### 3. Log in (no credentials needed)

Head to `http://localhost:5173/login` and pick a demo role:

| Role | Persona | What they can do |
|---|---|---|
| **Manager** | Alex Morgan | Email, calendar, voice commands, view team calendars, audit log |
| **Employee** | Jamie Lee | Own email and calendar only |
| **Admin** | Admin User | Everything, including the diagnostics panel |

---

## Docker

If you'd rather not set up Python and Node separately:

```bash
docker compose up --build
```

- App: `http://localhost:5173`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

---

## Demo mode

Everything works out of the box without any external accounts. Here's what swaps in when you're running in demo mode:

| Component | Demo mode | Live mode |
|---|---|---|
| Email & Calendar data | Realistic Contoso Corporation mock data | Live Microsoft 365 via Graph API |
| Speech-to-Text | Browser Web Speech API | OpenAI Whisper |
| Text-to-Speech | Browser `window.speechSynthesis` | OpenAI tts-1 |
| Authentication | Local mock login with role selector | Microsoft Azure AD OAuth 2.0 |
| Intent fallback | Regex rules engine only | Regex rules + GPT-4o-mini |

To switch to live integrations, fill in the relevant keys in `backend/.env` and flip the `USE_MOCK_*` flags to `false`.

---

## Voice commands

These all work out of the box in demo mode:

**Calendar**
```
What's on my calendar today?
Show me this week's meetings
Schedule a meeting with Sarah tomorrow at 2 PM
Book a one-hour check-in with Ali on Monday at 10
Delete my 3 PM meeting
```

**Email**
```
Read my emails
Summarise my inbox
Send an email to James about the project update
```

**Manager — team calendars**
```
Show Sarah's calendar
Check Jamie's schedule for this week
```

**Availability**
```
Am I free tomorrow afternoon?
Check availability for a meeting with the team on Friday
```

The intent engine runs deterministic regex rules first (30+ patterns with entity extraction). If confidence is low and the LLM fallback is enabled, it hands off to GPT-4o-mini.

---

## Configuration

Key variables in `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `APP_SECRET_KEY` | — | JWT signing secret (minimum 32 characters) |
| `USE_MOCK_GRAPH` | `true` | Use mock email/calendar data instead of live Graph API |
| `USE_MOCK_STT` | `true` | Disable backend Whisper (browser STT is used) |
| `USE_MOCK_TTS` | `true` | Disable OpenAI TTS (browser speechSynthesis is used) |
| `USE_LLM_INTENT` | `false` | Enable GPT-4o-mini intent fallback |
| `AZURE_TENANT_ID` | — | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | — | Azure AD app client ID |
| `AZURE_CLIENT_SECRET` | — | Azure AD app secret |
| `OPENAI_API_KEY` | — | Enables Whisper STT and tts-1 voice output |
| `MANAGER_EMAILS` | — | Comma-separated emails to assign Manager role |
| `ADMIN_EMAILS` | — | Comma-separated emails to assign Admin role |
| `DATABASE_URL` | `sqlite+aiosqlite:///./ipa.db` | Database connection string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | JWT expiry (8 hours) |

---

## Roles and permissions

| Permission | Employee | Manager | Admin |
|---|:---:|:---:|:---:|
| Read own email | ✓ | ✓ | ✓ |
| Send email | ✓ | ✓ | ✓ |
| Read own calendar | ✓ | ✓ | ✓ |
| Write own calendar | ✓ | ✓ | ✓ |
| Read team calendars | — | ✓ | ✓ |
| Schedule meetings | — | ✓ | ✓ |
| Modify any meeting | — | ✓ | ✓ |
| View audit log | — | ✓ | ✓ |
| Manage users | — | — | ✓ |
| Access diagnostics | — | — | ✓ |

---

## Project structure

```
ipa-corporate/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # FastAPI route handlers (voice, email, calendar, auth, audit, admin)
│   │   ├── core/                # config, security (JWT), RBAC, audit logger
│   │   ├── integrations/
│   │   │   └── graph/           # Microsoft Graph adapter (mock + real)
│   │   │   └── stt/             # Speech-to-text providers (mock, Whisper)
│   │   │   └── tts/             # Text-to-speech providers (mock, OpenAI, browser)
│   │   ├── intents/             # Hybrid intent classifier (rules engine + LLM parser)
│   │   ├── schemas/             # Pydantic request/response models
│   │   └── services/            # Business logic (email, calendar, voice)
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/          # Shared UI (AppShell, modals, layout)
│       ├── features/            # Domain panels (voice, email, calendar, audit, admin)
│       ├── hooks/               # useAuth, useVoice
│       ├── pages/               # Route-level page components
│       ├── services/api/        # Typed API client wrappers
│       └── types/               # TypeScript interfaces and enums
├── docs/                        # Architecture, security, API reference, demo guide
├── docker-compose.yml
└── Makefile
```

---

## Docs

| Document | What's in it |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | System design, component diagram, data flow |
| [`docs/requirements.md`](docs/requirements.md) | Functional and non-functional requirements |
| [`docs/security.md`](docs/security.md) | Threat model, STRIDE analysis, RBAC matrix |
| [`docs/testing.md`](docs/testing.md) | Testing strategy and coverage approach |
| [`docs/evaluation.md`](docs/evaluation.md) | SUS usability evaluation methodology |
| [`docs/api-reference.md`](docs/api-reference.md) | Full REST API endpoint reference |
| [`docs/demo-guide.md`](docs/demo-guide.md) | Demo script and viva Q&A prep |
| [`docs/risk-register.md`](docs/risk-register.md) | Project risk register |

---

## Audit logging

Every sensitive action — login, email read/send, calendar changes, employee calendar access, voice command classifications, permission denials — gets written to an append-only JSONL file at `backend/logs/audit.jsonl`. Managers and Admins can query it live via `/api/audit/logs`.

Email bodies and voice transcripts are never stored. Only the intent, actor, and outcome go into the log.

---

*Convo — Final Year Computing Project. The Contoso Corporation personas and data are fictional and used for demonstration purposes only.*
