# Convo — Voice Assistant for Corporate Managers

**Convo** is a browser-based voice assistant developed as a final-year computing project. It is designed to help corporate managers reduce the time spent triaging emails, managing calendars, and coordinating meetings.

Instead of navigating multiple applications, users can interact with Convo using natural language. For example:

> “Schedule a meeting with Sarah tomorrow at 2 PM.”

or:

> “Summarise my unread emails.”

Convo interprets the request, asks for confirmation when an action is potentially sensitive or destructive, and then carries out the task.

The application runs entirely in **demo mode out of the box**, so no Azure account or API keys are required to explore its core functionality.

---

## Features

### Voice and Text Commands

* Speak or type commands using natural language.
* Hybrid intent classification using:

  * Deterministic regex-based rules.
  * Optional GPT-4o-mini fallback for ambiguous requests.
* Entity extraction for dates, times, people, and actions.

### Email

* Read inbox messages.
* View individual emails.
* Generate AI-powered email summaries.
* Compose and send emails.
* Require confirmation before sending emails.

### Calendar

* View today's schedule.
* View the full week's schedule.
* Create meetings.
* Update existing meetings.
* Delete meetings.
* Check availability.

### Manager Team View

* Managers can view team members' calendars.
* Employees can only access their own calendars.
* Access is enforced through role-based permissions.

### Role-Based Access Control

Convo provides three user roles:

* **Employee**
* **Manager**
* **Admin**

Permissions are enforced across API routes using a central RBAC system.

### Confirmation Flow

Potentially risky actions are staged before execution.

For example:

> “Delete my 3 PM meeting.”

Convo first prepares the deletion and waits for confirmation before carrying it out.

This applies to actions such as:

* Sending emails.
* Deleting meetings.
* Other sensitive operations.

### Audit Trail

Sensitive actions are recorded in an append-only audit log.

Logged events include:

* Login attempts.
* Email access and sending.
* Calendar modifications.
* Team calendar access.
* Voice command classifications.
* Permission denials.

**Email bodies and voice transcripts are never stored.**

---

## Tech Stack

| Layer                 | Technology                              | Version          |
| --------------------- | --------------------------------------- | ---------------- |
| Backend framework     | FastAPI + Uvicorn                       | 0.111 / 0.29     |
| Data validation       | Pydantic v2                             | 2.7.1            |
| Authentication        | MSAL + python-jose (JWT HS256)          | 1.28 / 3.3       |
| Password hashing      | Passlib + bcrypt                        | 1.7.4            |
| HTTP client           | httpx                                   | 0.27             |
| Database / ORM        | SQLAlchemy + aiosqlite                  | 2.0.30           |
| Database migrations   | Alembic                                 | 1.13.1           |
| Microsoft integration | Microsoft Graph REST API v1.0           | —                |
| Speech-to-text        | Browser Web Speech API / OpenAI Whisper | —                |
| Text-to-speech        | Browser speechSynthesis / OpenAI TTS    | —                |
| Logging               | structlog                               | 24.1             |
| Frontend              | React + TypeScript + Vite               | 18.3 / 5.4 / 5.2 |
| Server state          | TanStack Query                          | 5.40             |
| Client state          | Zustand                                 | 4.5              |
| Styling               | Tailwind CSS                            | 3.4              |
| Routing               | React Router                            | 6.23             |
| Icons                 | Lucide React                            | 0.379            |

---

## Getting Started

### Prerequisites

You will need:

* Python 3.11+
* Node.js 18+
* Chrome or Edge for microphone access and the Web Speech API

The following are **optional** and only required for live integrations:

* Azure AD application registration
* OpenAI API key

### 1. Start the Backend

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

The backend API will be available at:

`http://localhost:8000`

Interactive API documentation:

`http://localhost:8000/docs`

### 2. Start the Frontend

```bash
cd frontend

npm install
npm run dev
```

The frontend will be available at:

`http://localhost:5173`

### 3. Log In

Open:

`http://localhost:5173/login`

No credentials are required in demo mode. Select one of the available demo roles:

| Role         | Persona     | Capabilities                                               |
| ------------ | ----------- | ---------------------------------------------------------- |
| **Manager**  | Alex Morgan | Email, calendar, voice commands, team calendars, audit log |
| **Employee** | Jamie Lee   | Own email and calendar                                     |
| **Admin**    | Admin User  | All features, including diagnostics                        |

---

## Docker

If you prefer not to install Python and Node.js dependencies separately, you can run the entire application using Docker:

```bash
docker compose up --build
```

The services will be available at:

| Service           | URL                          |
| ----------------- | ---------------------------- |
| Application       | `http://localhost:5173`      |
| API               | `http://localhost:8000`      |
| API documentation | `http://localhost:8000/docs` |

---

## Demo Mode

Convo is designed to work without external accounts or API keys.

Demo mode replaces external services with local implementations and realistic mock data.

| Component        | Demo Mode                               | Live Mode                    |
| ---------------- | --------------------------------------- | ---------------------------- |
| Email & Calendar | Realistic Contoso Corporation mock data | Microsoft 365 via Graph API  |
| Speech-to-Text   | Browser Web Speech API                  | OpenAI Whisper               |
| Text-to-Speech   | Browser `speechSynthesis`               | OpenAI TTS                   |
| Authentication   | Local mock login with role selection    | Microsoft Azure AD OAuth 2.0 |
| Intent fallback  | Regex rules only                        | Regex rules + GPT-4o-mini    |

To enable live integrations, configure the relevant environment variables in `backend/.env` and set the appropriate `USE_MOCK_*` flags to `false`.

---

## Example Voice Commands

All of the following commands work in demo mode.

### Calendar

```text
What's on my calendar today?
Show me this week's meetings.
Schedule a meeting with Sarah tomorrow at 2 PM.
Book a one-hour check-in with Ali on Monday at 10.
Delete my 3 PM meeting.
```

### Email

```text
Read my emails.
Summarise my inbox.
Send an email to James about the project update.
```

### Manager Team Calendars

```text
Show Sarah's calendar.
Check Jamie's schedule for this week.
```

### Availability

```text
Am I free tomorrow afternoon?
Check availability for a meeting with the team on Friday.
```

The intent engine first evaluates requests using a deterministic regex rules engine containing 30+ patterns with entity extraction.

If confidence is low and the LLM fallback is enabled, the request can be passed to GPT-4o-mini for further interpretation.

---

## Configuration

The main configuration options are stored in `backend/.env`.

| Variable                      | Default                        | Description                                                |
| ----------------------------- | ------------------------------ | ---------------------------------------------------------- |
| `APP_SECRET_KEY`              | —                              | JWT signing secret. Minimum 32 characters.                 |
| `USE_MOCK_GRAPH`              | `true`                         | Use mock email/calendar data instead of Microsoft Graph.   |
| `USE_MOCK_STT`                | `true`                         | Disable backend Whisper and use browser STT.               |
| `USE_MOCK_TTS`                | `true`                         | Disable OpenAI TTS and use browser speech synthesis.       |
| `USE_LLM_INTENT`              | `false`                        | Enable GPT-4o-mini intent fallback.                        |
| `AZURE_TENANT_ID`             | —                              | Azure AD tenant ID.                                        |
| `AZURE_CLIENT_ID`             | —                              | Azure AD application/client ID.                            |
| `AZURE_CLIENT_SECRET`         | —                              | Azure AD application secret.                               |
| `OPENAI_API_KEY`              | —                              | Enables Whisper and OpenAI TTS integrations.               |
| `MANAGER_EMAILS`              | —                              | Comma-separated email addresses assigned the Manager role. |
| `ADMIN_EMAILS`                | —                              | Comma-separated email addresses assigned the Admin role.   |
| `DATABASE_URL`                | `sqlite+aiosqlite:///./ipa.db` | Database connection string.                                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480`                          | JWT expiration time in minutes.                            |

---

## Roles and Permissions

| Permission          | Employee | Manager | Admin |
| ------------------- | :------: | :-----: | :---: |
| Read own email      |     ✓    |    ✓    |   ✓   |
| Send email          |     ✓    |    ✓    |   ✓   |
| Read own calendar   |     ✓    |    ✓    |   ✓   |
| Write own calendar  |     ✓    |    ✓    |   ✓   |
| Read team calendars |     —    |    ✓    |   ✓   |
| Schedule meetings   |     —    |    ✓    |   ✓   |
| Modify any meeting  |     —    |    ✓    |   ✓   |
| View audit log      |     —    |    ✓    |   ✓   |
| Manage users        |     —    |    —    |   ✓   |
| Access diagnostics  |     —    |    —    |   ✓   |

---

## Project Structure

```text
ipa-corporate/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # FastAPI route handlers
│   │   │                             # voice, email, calendar, auth, audit, admin
│   │   ├── core/                # Configuration, security, RBAC, audit logging
│   │   ├── integrations/
│   │   │   ├── graph/           # Microsoft Graph adapter (mock + real)
│   │   │   ├── stt/             # Speech-to-text providers
│   │   │   └── tts/             # Text-to-speech providers
│   │   ├── intents/              # Hybrid intent classifier
│   │   ├── schemas/              # Pydantic request/response models
│   │   └── services/             # Email, calendar and voice business logic
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/           # Shared UI components
│       ├── features/             # Voice, email, calendar, audit and admin
│       ├── hooks/                # useAuth, useVoice
│       ├── pages/                # Route-level page components
│       ├── services/
│       │   └── api/              # Typed API client wrappers
│       └── types/                # TypeScript interfaces and enums
│
├── docs/                         # Project documentation
├── docker-compose.yml
└── Makefile
```

---

## Documentation

| Document                                         | Description                                    |
| ------------------------------------------------ | ---------------------------------------------- |
| [`docs/architecture.md`](docs/architecture.md)   | System design, component diagram and data flow |
| [`docs/requirements.md`](docs/requirements.md)   | Functional and non-functional requirements     |
| [`docs/security.md`](docs/security.md)           | Threat model, STRIDE analysis and RBAC matrix  |
| [`docs/testing.md`](docs/testing.md)             | Testing strategy and coverage approach         |
| [`docs/evaluation.md`](docs/evaluation.md)       | SUS usability evaluation methodology           |
| [`docs/api-reference.md`](docs/api-reference.md) | REST API endpoint reference                    |
| [`docs/demo-guide.md`](docs/demo-guide.md)       | Demo script and viva preparation               |
| [`docs/risk-register.md`](docs/risk-register.md) | Project risk register                          |

---

## Audit Logging

Every sensitive operation is recorded in an append-only JSONL audit file:

```text
backend/logs/audit.jsonl
```

Examples of logged events include:

* Login attempts
* Email reads and sends
* Calendar changes
* Employee calendar access
* Voice command classifications
* Permission denials

Managers and Administrators can query the audit log through:

```text
/api/audit/logs
```

The audit system intentionally avoids storing sensitive content.

**Email bodies and voice transcripts are never stored.** Only relevant metadata, such as the actor, action, intent, and outcome, is recorded.

---

## Project Scope and Demo Data

Convo uses fictional **Contoso Corporation** personas and data for demonstration purposes.

The project is intended as a final-year computing project demonstrating:

* Voice-based human-computer interaction
* Natural-language intent classification
* Role-based access control
* Microsoft Graph integration
* Confirmation-based action workflows
* Secure audit logging
* Modern full-stack web development

All Contoso Corporation data and personas included in the application are fictional and used solely for demonstration purposes.

---

## License

This project was developed as part of a final-year computing project.
