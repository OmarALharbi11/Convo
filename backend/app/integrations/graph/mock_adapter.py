"""
Mock Microsoft Graph adapters for offline/demo/testing use.

Provides the same interface as the live adapters but returns hard-coded,
realistic corporate data.  Selected via USE_MOCK_GRAPH=true in .env.

Mock data represents "Contoso Corporation" — a fictitious company used
throughout the project's demo scenarios.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.calendar import (
    AvailabilityRequest,
    AvailabilityResponse,
    AvailabilitySlot,
    CalendarEvent,
    CalendarEventList,
    CreateEventRequest,
    UpdateEventRequest,
)
from app.schemas.email import (
    EmailFilter,
    EmailListResponse,
    EmailMessage,
    EmailSummary,
    SendEmailRequest,
    SendEmailResponse,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Mock email data
# ---------------------------------------------------------------------------

# Manager inbox — strategic, financial, team management
_MOCK_EMAILS_MANAGER: list[dict[str, Any]] = [
    {
        "id": "mgr-001",
        "subject": "Q3 Financial Review — Action Required",
        "sender_name": "David Walsh",
        "sender_email": "d.walsh@contoso.com",
        "received_at": _now() - timedelta(hours=1),
        "is_read": False,
        "preview": "Please review the attached Q3 financial summary before Thursday's board meeting. Key variances have been highlighted...",
        "body_text": (
            "Hi Alex,\n\n"
            "I'm writing ahead of Thursday's board meeting to flag several items that require your review and sign-off before we present to the executive committee.\n\n"
            "The Q3 financial summary has been finalised by the finance team and is attached to this email. In brief, we are tracking 4% below the revenue target for the quarter, primarily driven by delays in the EMEA region's enterprise contract renewals. The CFO has highlighted three line items in red that require managerial justification before the board pack is submitted.\n\n"
            "Key variances requiring your attention:\n"
            "- EMEA enterprise renewals: £340K shortfall vs. plan (delayed to Q4)\n"
            "- Professional services overspend: £82K above budget due to the Project Phoenix extension\n"
            "- Headcount savings: £55K favourable, offset partially by contractor spend\n\n"
            "I also want to flag that the board will likely ask about our Q4 pipeline confidence. I'd recommend we prepare a brief slide on the three deals currently at contract stage — I can draft this if helpful.\n\n"
            "Please could you review the attached and provide your sign-off comments by EOD Wednesday. If you have concerns that require a pre-meeting discussion, I'm available Tuesday afternoon from 3pm onwards.\n\n"
            "Best regards,\nDavid Walsh\nHead of Finance, Contoso Corporation"
        ),
        "importance": "high",
    },
    {
        "id": "mgr-002",
        "subject": "URGENT: Client Escalation — Acme Corp",
        "sender_name": "Emma Thompson",
        "sender_email": "e.thompson@contoso.com",
        "received_at": _now() - timedelta(hours=2),
        "is_read": False,
        "preview": "We have received a P1 escalation from Acme Corp regarding the data export feature. They are threatening to escalate to executive level...",
        "body_text": (
            "Alex,\n\n"
            "I need to bring an urgent client issue to your attention immediately. Acme Corp have raised a P1 escalation at 09:14 this morning regarding our data export feature.\n\n"
            "Background: Their data warehouse team ran a bulk export job overnight on approximately 2.3 million records. The exported CSV files are missing the 'created_by' and 'last_modified' columns entirely. Their finance team has been unable to complete a regulatory audit submission that was due this morning as a result.\n\n"
            "Their account director, Marcus Reid, called me directly at 09:30 and stated that if we do not provide a resolution path within two hours, he will escalate to our CEO and their legal team. He referenced clause 8.4 of their SLA which guarantees 99.9% data integrity on export operations.\n\n"
            "I have already looped in the engineering team (ticket #ENG-4421 raised) and the initial assessment suggests a schema migration deployed last Thursday may have dropped those columns from the export query. A hotfix is being assessed — initial estimate is 4–6 hours to deploy.\n\n"
            "What I need from you:\n"
            "1. Authorisation to offer Acme a service credit as goodwill (I'd suggest £2,500 or one month's subscription)\n"
            "2. Confirmation you're available to join a call with Marcus Reid at 11:00 if needed\n"
            "3. Decision on whether to notify other enterprise clients who may be affected\n\n"
            "I will send a holding response to Acme now confirming we are investigating. Please respond as soon as possible.\n\n"
            "Emma Thompson\nSenior Account Manager"
        ),
        "importance": "high",
    },
    {
        "id": "mgr-003",
        "subject": "Team Standup Notes — Monday",
        "sender_name": "Sarah Connor",
        "sender_email": "s.connor@contoso.com",
        "received_at": _now() - timedelta(hours=3),
        "is_read": False,
        "preview": "Hi all, attaching the notes from this morning's standup. Key blockers: API integration delayed by 2 days...",
        "body_text": (
            "Hi all,\n\n"
            "Here are the notes from this morning's team standup. Please review and flag any corrections.\n\n"
            "ATTENDEES: Alex Morgan, Sarah Connor, John Smith, Priya Patel, Tom Hughes\n"
            "ABSENT: Jamie Lee (sick leave)\n\n"
            "PROGRESS UPDATES:\n"
            "- John: Completed the OAuth token refresh logic. PR is up for review (IPA-211). Currently working on rate-limit handling.\n"
            "- Priya: UI components for the calendar view are 80% complete. Blocked on final API contract for the availability endpoint.\n"
            "- Tom: Finished unit tests for the email service layer. Coverage now at 87%. Starting integration tests today.\n\n"
            "BLOCKERS:\n"
            "- API integration (IPA-214) is delayed by 2 days. The upstream Microsoft Graph sandbox is returning inconsistent responses on the availability endpoint. John is liaising with their developer support team. New ETA: Wednesday EOB.\n"
            "- Priya cannot finalise the calendar UI until the availability API contract is confirmed. This creates a downstream dependency risk for the sprint demo.\n\n"
            "NOTES:\n"
            "- John is OOO Thursday and Friday (pre-booked leave). Please plan reviews accordingly.\n"
            "- Sprint demo is Thursday 3pm — Sarah to confirm room booking.\n"
            "- Alex: please review and approve the revised sprint scope by noon Tuesday (shared in Confluence).\n\n"
            "Next standup: Tuesday 9:30am.\n\n"
            "Thanks,\nSarah Connor\nDelivery Lead"
        ),
        "importance": "normal",
    },
    {
        "id": "mgr-004",
        "subject": "Board Presentation — Slide Deck Draft",
        "sender_name": "David Walsh",
        "sender_email": "d.walsh@contoso.com",
        "received_at": _now() - timedelta(hours=4),
        "is_read": True,
        "preview": "Attached is the draft slide deck for the board presentation. Please review slides 8–12 covering the headcount forecast...",
        "body_text": (
            "Alex,\n\n"
            "Please find attached the draft slide deck for Thursday's board presentation. The deck is 24 slides and covers the standard quarterly update format.\n\n"
            "I would particularly appreciate your review of slides 8 through 12, which cover the headcount and hiring forecast for Q4 and FY2027. These slides contain assumptions that I'd like you to validate before we lock the narrative:\n\n"
            "- Slide 8: Current headcount by department (pulled from HR system as of Friday — please check engineering numbers are accurate)\n"
            "- Slide 9: Planned hires Q4 — shows 4 engineering, 2 sales, 1 finance. Is this still the plan?\n"
            "- Slide 10: Attrition risk matrix — I've flagged 3 individuals as 'high risk'. You may want to review this before it goes to the board.\n"
            "- Slide 11: Salary band review timeline — I've indicated this will be completed by end of Q4. Please confirm.\n"
            "- Slide 12: Total payroll cost projection — uses 3.5% uplift assumption. Finance sign-off is needed here.\n\n"
            "Other sections (revenue, product roadmap, customer metrics) have already been reviewed by the respective heads. I'm waiting on your comments before sending to the CEO for final sign-off.\n\n"
            "Deadline for comments: Today by 5pm please, so I can incorporate changes before the print run tomorrow morning.\n\n"
            "Thanks,\nDavid"
        ),
        "importance": "high",
    },
    {
        "id": "mgr-005",
        "subject": "Re: Project Phoenix — Deployment Window",
        "sender_name": "IT Operations",
        "sender_email": "it.ops@contoso.com",
        "received_at": _now() - timedelta(hours=5),
        "is_read": True,
        "preview": "Confirming the deployment window for Project Phoenix: Saturday 02:00–06:00 UTC. Please ensure the on-call rota is updated...",
        "body_text": (
            "Hi Alex,\n\n"
            "Following the CAB approval yesterday, we are confirming the deployment window for Project Phoenix Release 3.2.1.\n\n"
            "DEPLOYMENT DETAILS:\n"
            "- Window: Saturday 02:00–06:00 UTC (4-hour window)\n"
            "- Services affected: Core API, reporting engine, data pipeline scheduler\n"
            "- Expected downtime: ~35 minutes for the API layer during database migration\n"
            "- Rollback time (if triggered): ~20 minutes\n\n"
            "PRE-DEPLOYMENT CHECKLIST (requires sign-off by Friday 17:00):\n"
            "[ ] Database migration script reviewed by DBA — DONE (Tom H, signed off 14:22)\n"
            "[ ] Load test results reviewed — DONE (passed at 120% projected load)\n"
            "[ ] Rollback plan approved — PENDING your sign-off\n"
            "[ ] Customer communications sent — DONE (maintenance window notice sent Tuesday)\n"
            "[ ] On-call engineer confirmed — PENDING (please update the rota, current gap: 03:00–04:30)\n\n"
            "ACTION REQUIRED:\n"
            "Please review and sign off the rollback plan (attached) and ensure the on-call rota gap is filled before Friday close of business. Without these two items, we will be unable to proceed with the deployment as scheduled.\n\n"
            "Contact me directly if you have any concerns.\n\n"
            "Regards,\nIT Operations Team\nContoso Corporation"
        ),
        "importance": "normal",
    },
    {
        "id": "mgr-006",
        "subject": "Invoice #4521 — Approved",
        "sender_name": "Finance Team",
        "sender_email": "finance@contoso.com",
        "received_at": _now() - timedelta(days=2),
        "is_read": True,
        "preview": "Invoice #4521 from Cloud Solutions Ltd has been approved for payment. Amount: £12,450. Payment scheduled for next Tuesday...",
        "body_text": (
            "Dear Alex,\n\n"
            "This is a notification that the following invoice has been reviewed, approved, and scheduled for payment.\n\n"
            "INVOICE DETAILS:\n"
            "- Supplier: Cloud Solutions Ltd\n"
            "- Invoice number: #4521\n"
            "- Invoice date: 22 March 2026\n"
            "- Amount: £12,450.00 (excl. VAT)\n"
            "- VAT (20%): £2,490.00\n"
            "- Total payable: £14,940.00\n"
            "- Cost centre: Engineering — Infrastructure (CC-0047)\n"
            "- Purchase order: PO-2026-0183\n\n"
            "APPROVAL DETAILS:\n"
            "- Approved by: David Walsh (Head of Finance)\n"
            "- Approval date: 28 March 2026\n"
            "- Payment method: BACS\n"
            "- Scheduled payment date: Tuesday 2 April 2026\n\n"
            "This invoice covers the monthly cloud infrastructure hosting fees for March 2026, including the additional storage provisioned for the Project Phoenix data pipeline.\n\n"
            "If you have any queries regarding this payment, please contact the finance team referencing invoice #4521.\n\n"
            "Finance Team\nContoso Corporation"
        ),
        "importance": "normal",
    },
]

# Employee inbox — project tasks, team updates, HR notices
_MOCK_EMAILS_EMPLOYEE: list[dict[str, Any]] = [
    {
        "id": "emp-001",
        "subject": "Your Tasks for This Sprint — Sprint 14",
        "sender_name": "Sarah Connor",
        "sender_email": "s.connor@contoso.com",
        "received_at": _now() - timedelta(hours=1),
        "is_read": False,
        "preview": "Hi Jamie, here are your assigned tickets for Sprint 14. Please update Jira with your estimates by end of day...",
        "body_text": (
            "Hi Jamie,\n\n"
            "Hope you're feeling better after your sick day. Here's a summary of your assigned tickets for Sprint 14, which started this morning.\n\n"
            "ASSIGNED TO YOU — SPRINT 14:\n\n"
            "IPA-214 | API Integration — Graph availability endpoint\n"
            "Priority: High | Estimate: 3 days\n"
            "The upstream sandbox is returning inconsistent responses. John has been in touch with Microsoft Developer Support and has a fix coming. You'll need to integrate and test once his PR (IPA-211) is merged. Please pull the latest from main before starting.\n\n"
            "IPA-219 | Unit tests — Email service layer\n"
            "Priority: Medium | Estimate: 1.5 days\n"
            "Tom has already achieved 87% coverage on the core service. Your task is to cover the edge cases in the summarisation engine — specifically the null body_text path and the sentiment detection when both positive and negative words appear. Tests should be in /tests/test_email_service.py.\n\n"
            "IPA-221 | Documentation — REST API reference\n"
            "Priority: Low | Estimate: 0.5 days\n"
            "Update the OpenAPI descriptions for all new endpoints added in Sprint 13. Mainly the /calendar/availability and /voice/confirm routes. Use the existing style in the other route files as a guide.\n\n"
            "REMINDERS:\n"
            "- Please update your Jira estimates and start dates by EOD today\n"
            "- Sprint demo is Thursday 3pm, Room 4B — attendance required\n"
            "- If you're going to miss the IPA-214 deadline, flag it to me by Tuesday noon so I can replan\n\n"
            "Let me know if you have any questions.\n\n"
            "Sarah"
        ),
        "importance": "normal",
    },
    {
        "id": "emp-002",
        "subject": "Reminder: Annual Leave Request Deadline",
        "sender_name": "HR Team",
        "sender_email": "hr@contoso.com",
        "received_at": _now() - timedelta(hours=2),
        "is_read": False,
        "preview": "This is a reminder that all annual leave requests for Q4 must be submitted via the HR portal by Friday 5pm...",
        "body_text": (
            "Dear Jamie,\n\n"
            "This is a reminder that the deadline for submitting Q4 annual leave requests is this Friday at 5:00pm.\n\n"
            "As of today, our records show that you have 8 days of annual leave remaining for the 2026 leave year, which ends on 31 December 2026. Under our leave policy, a maximum of 5 days may be carried over into the next leave year. We therefore encourage you to plan and book your remaining leave to avoid any forfeiture.\n\n"
            "HOW TO REQUEST LEAVE:\n"
            "1. Log in to the HR portal at hr.contoso.com\n"
            "2. Navigate to 'My Leave' → 'Request Leave'\n"
            "3. Select your dates and leave type (Annual Leave)\n"
            "4. Submit for manager approval\n\n"
            "IMPORTANT NOTES:\n"
            "- Requests submitted after Friday 5pm cannot be guaranteed for Q4 dates, particularly around the December holiday period which is already heavily booked\n"
            "- The festive shutdown period (24 Dec – 2 Jan) requires separate booking via the HR portal under 'Festive Shutdown'\n"
            "- If you have any extenuating circumstances, please contact your HR Business Partner directly\n\n"
            "If you have already submitted your Q4 leave requests and received manager approval, please disregard this reminder.\n\n"
            "Kind regards,\nHR Team\nContoso Corporation\nhr@contoso.com | Ext. 2100"
        ),
        "importance": "normal",
    },
    {
        "id": "emp-003",
        "subject": "New Security Policy — Mandatory Reading",
        "sender_name": "Security Team",
        "sender_email": "security@contoso.com",
        "received_at": _now() - timedelta(hours=4),
        "is_read": False,
        "preview": "A revised information security policy has been issued. All staff must complete the acknowledgement form by Friday...",
        "body_text": (
            "Dear All,\n\n"
            "The Information Security team has published a revised Information Security Policy (v4.2), effective immediately. All employees are required to read the policy and complete the mandatory acknowledgement form by this Friday.\n\n"
            "WHAT HAS CHANGED IN v4.2:\n"
            "The key changes from the previous version (v4.1) are summarised below. Full details are in the attached policy document.\n\n"
            "1. Remote working — new requirements for VPN usage when accessing internal systems from non-office locations. The 'trusted home network' exemption has been removed.\n\n"
            "2. Password policy — minimum password length increased from 10 to 14 characters. Multi-factor authentication (MFA) is now mandatory for all systems, not just email and VPN. Your IT team will be in touch separately about any accounts not yet enrolled in MFA.\n\n"
            "3. Data classification — a new 'Restricted' tier has been added above 'Confidential'. Client financial data, personal data, and legal correspondence must now be classified as Restricted and may only be stored in approved encrypted locations.\n\n"
            "4. Incident reporting — the reporting window for suspected security incidents has been reduced from 72 hours to 24 hours. The new reporting form is available at security.contoso.com/report.\n\n"
            "5. Personal device usage — personal devices (BYOD) are no longer permitted to access corporate email or systems unless enrolled in Mobile Device Management (MDM). Contact IT to enrol your device.\n\n"
            "ACTION REQUIRED:\n"
            "Please read the attached policy and complete the acknowledgement form at hr.contoso.com/security-acknowledgement by Friday 5pm. Non-completion will be escalated to your line manager.\n\n"
            "Questions? Contact the Security team at security@contoso.com or raise a ticket at helpdesk.contoso.com.\n\n"
            "Information Security Team\nContoso Corporation"
        ),
        "importance": "high",
    },
    {
        "id": "emp-004",
        "subject": "Sprint Review Invitation — Thursday 3PM",
        "sender_name": "Sarah Connor",
        "sender_email": "s.connor@contoso.com",
        "received_at": _now() - timedelta(hours=8),
        "is_read": True,
        "preview": "You are invited to the Sprint 14 Review on Thursday at 3 PM in Room 4B. Demo agenda attached...",
        "body_text": (
            "Hi team,\n\n"
            "You're invited to the Sprint 14 Review and Retrospective, taking place this Thursday at 3:00pm in Room 4B (capacity 12, projector booked).\n\n"
            "AGENDA:\n"
            "15:00 — Welcome and sprint summary (Sarah, 5 mins)\n"
            "15:05 — Demo: Voice command pipeline (John, 15 mins)\n"
            "15:20 — Demo: Calendar integration and availability check (Priya, 10 mins)\n"
            "15:30 — Demo: Email summarisation feature (Jamie, 10 mins)\n"
            "15:40 — Stakeholder Q&A (Alex Morgan attending, 10 mins)\n"
            "15:50 — Retrospective — what went well / what to improve (15 mins)\n"
            "16:05 — Sprint 15 planning preview (Sarah, 10 mins)\n"
            "16:15 — Close\n\n"
            "PREPARATION:\n"
            "- Please have your demo environment ready and tested before 2:45pm\n"
            "- Jamie: please prepare a 2-slide summary of the email summarisation accuracy results from your testing\n"
            "- If you have retrospective items to raise, add them to the Miro board (link in Confluence) before Thursday morning\n\n"
            "ATTENDANCE:\n"
            "This is a mandatory team event. If you cannot attend, please notify me by Wednesday noon so I can adjust the agenda. Alex Morgan (Engineering Manager) and David Walsh (Finance) will be observing the demos.\n\n"
            "Please confirm your attendance by replying to this email.\n\n"
            "Thanks,\nSarah"
        ),
        "importance": "normal",
    },
    {
        "id": "emp-005",
        "subject": "Holiday Party Planning — Save the Date",
        "sender_name": "HR Team",
        "sender_email": "hr@contoso.com",
        "received_at": _now() - timedelta(days=1),
        "is_read": True,
        "preview": "The annual company holiday party is confirmed for 15th December. Venue: The Grand Hotel. Tickets are available via the HR portal...",
        "body_text": (
            "Dear all,\n\n"
            "We're delighted to confirm that the Contoso Corporation Annual Holiday Party will take place on Saturday 15th December 2026!\n\n"
            "EVENT DETAILS:\n"
            "- Date: Saturday, 15 December 2026\n"
            "- Venue: The Grand Hotel, 27 Victoria Embankment, London\n"
            "- Drinks reception: 7:00pm\n"
            "- Dinner: 8:00pm\n"
            "- Dancing and entertainment: 10:00pm – 1:00am\n"
            "- Dress code: Black tie / formal\n\n"
            "TICKETS:\n"
            "Each employee is entitled to one complimentary ticket. Partner/guest tickets are available at a subsidised rate of £35 per person (normally £95). Tickets must be purchased via the HR portal by Friday 14th November. Numbers are capped at 180 — tickets will be allocated on a first-come, first-served basis.\n\n"
            "HOTEL ACCOMMODATION:\n"
            "We have negotiated a discounted rate of £129/night (standard double) at The Grand Hotel for attendees. To book, use the code CONTOSO2026 when reserving via the hotel's website. This rate is available for the nights of Friday 14th and Saturday 15th December only. We recommend booking early as rooms are limited.\n\n"
            "To purchase your ticket or find out more, log in to the HR portal at hr.contoso.com and navigate to 'Events'.\n\n"
            "We look forward to celebrating with you all!\n\n"
            "HR Team\nContoso Corporation"
        ),
        "importance": "low",
    },
    {
        "id": "emp-006",
        "subject": "Peer Review: IPA-198 — Please action",
        "sender_name": "John Smith",
        "sender_email": "j.smith@contoso.com",
        "received_at": _now() - timedelta(hours=6),
        "is_read": False,
        "preview": "Hey Jamie, could you take a look at my PR for IPA-198 when you get a moment? Mainly changes to the auth middleware...",
        "body_text": (
            "Hey Jamie,\n\n"
            "Hope you're back on your feet! When you get a moment, could you take a look at my PR for IPA-198?\n\n"
            "PR link: github.com/contoso/ipa-corporate/pull/87\n\n"
            "WHAT THE PR DOES:\n"
            "This PR reworks the JWT authentication middleware to fix a token expiry edge case that was causing silent 401 failures for long-running sessions. The main changes are:\n\n"
            "1. Token refresh logic — added a pre-emptive refresh when the token has less than 5 minutes until expiry, rather than waiting for the 401 response. This eliminates the ~2 second interruption users were experiencing mid-session.\n\n"
            "2. Error handling — improved the error messages returned when token validation fails. Previously everything returned a generic 401; now the client receives a specific error code (TOKEN_EXPIRED, TOKEN_INVALID, TOKEN_MISSING) so the frontend can handle each case appropriately.\n\n"
            "3. Test coverage — added 6 new unit tests covering the expiry edge cases. All existing tests still pass.\n\n"
            "WHAT I'D LIKE YOU TO REVIEW:\n"
            "- The refresh logic in /app/core/security.py lines 84–112 — I'm not 100% happy with the approach and would value a second opinion\n"
            "- The new tests in /tests/test_security.py — please check I've covered the right scenarios\n"
            "- Any general code quality comments welcome\n\n"
            "I've addressed all comments from the previous review (thanks for those). Changes are marked with inline comments.\n\n"
            "No rush if you're catching up from being off, but ideally before Thursday so it can go into the sprint demo build.\n\n"
            "Cheers,\nJohn"
        ),
        "importance": "normal",
    },
]

# Admin inbox — system alerts, platform notices, security
_MOCK_EMAILS_ADMIN: list[dict[str, Any]] = [
    {
        "id": "adm-001",
        "subject": "CRITICAL: Failed login attempts detected",
        "sender_name": "Security Monitoring",
        "sender_email": "security-alerts@contoso.com",
        "received_at": _now() - timedelta(minutes=30),
        "is_read": False,
        "preview": "15 failed login attempts detected from IP 185.220.101.42 targeting the admin portal. Account lockout triggered...",
        "body_text": (
            "AUTOMATED SECURITY ALERT — PRIORITY: CRITICAL\n\n"
            "This alert was generated automatically by the Contoso Security Monitoring Platform at 09:14 UTC.\n\n"
            "INCIDENT SUMMARY:\n"
            "15 consecutive failed authentication attempts have been detected against the administrative portal (admin.contoso.com) originating from the following IP address:\n\n"
            "Source IP: 185.220.101.42\n"
            "Geolocation: Tor exit node — country of origin unknown\n"
            "Target account: j.smith@contoso.com\n"
            "Attack pattern: Credential stuffing (dictionary-based)\n"
            "Time of first attempt: 09:08:33 UTC\n"
            "Time of last attempt: 09:14:01 UTC\n\n"
            "AUTOMATED ACTIONS TAKEN:\n"
            "- Account j.smith@contoso.com has been temporarily locked (30-minute lockout)\n"
            "- IP 185.220.101.42 has been added to the WAF block list\n"
            "- SIEM ticket #SEC-2847 has been auto-created\n\n"
            "RECOMMENDED ACTIONS:\n"
            "1. Verify with j.smith@contoso.com that this was not a legitimate access attempt (e.g. forgotten password)\n"
            "2. Review the full access log for this account over the past 7 days (link below)\n"
            "3. Check whether any other accounts were targeted from this IP — see the detailed report attached\n"
            "4. If suspicious activity is confirmed, initiate the Incident Response procedure under IS-POL-003\n"
            "5. Consider resetting j.smith's credentials and enforcing MFA re-enrolment\n\n"
            "Access log: admin.contoso.com/logs/auth?ip=185.220.101.42\n"
            "SIEM ticket: siem.contoso.com/incidents/SEC-2847\n\n"
            "If you believe this alert was triggered in error, please close the SIEM ticket with justification.\n\n"
            "Contoso Security Monitoring Platform\nDo not reply to this email."
        ),
        "importance": "high",
    },
    {
        "id": "adm-002",
        "subject": "Azure AD — New guest user provisioned",
        "sender_name": "Azure Active Directory",
        "sender_email": "azure-noreply@microsoft.com",
        "received_at": _now() - timedelta(hours=1),
        "is_read": False,
        "preview": "A new guest user account has been provisioned in your tenant: contractor.jones@external.com. Invited by: e.thompson@contoso.com...",
        "body_text": (
            "AZURE ACTIVE DIRECTORY NOTIFICATION\n\n"
            "A new guest user account has been provisioned in the Contoso Corporation Azure AD tenant.\n\n"
            "GUEST USER DETAILS:\n"
            "- Display name: Marcus Jones\n"
            "- Email: contractor.jones@external.com\n"
            "- Account type: Guest (B2B collaboration)\n"
            "- Invited by: Emma Thompson (e.thompson@contoso.com)\n"
            "- Invitation accepted: Yes — 28 March 2026, 10:47 UTC\n"
            "- Account created: 28 March 2026, 10:47 UTC\n\n"
            "GROUPS ASSIGNED:\n"
            "- Contractors-ReadOnly (auto-assigned by invitation policy)\n\n"
            "ACCESS CURRENTLY GRANTED:\n"
            "- SharePoint: Contoso-ProjectPhoenix-External (read only)\n"
            "- Teams: Project Phoenix External channel\n\n"
            "ACTION RECOMMENDED:\n"
            "As administrator, please review this guest account to ensure:\n"
            "1. The invitation was authorised under the Third-Party Access Request process (form TP-001)\n"
            "2. The access granted is appropriate and limited to business need\n"
            "3. An expiry date has been set for the guest account (recommended: contract end date)\n"
            "4. The account is documented in the Third-Party Access Register\n\n"
            "Guest accounts without a documented business justification will be reviewed and may be removed during the next quarterly access audit.\n\n"
            "To manage this account: portal.azure.com → Azure Active Directory → External Identities\n\n"
            "Microsoft Azure\nThis is an automated notification. Do not reply."
        ),
        "importance": "high",
    },
    {
        "id": "adm-003",
        "subject": "Monthly Licence Report — October",
        "sender_name": "IT Operations",
        "sender_email": "it.ops@contoso.com",
        "received_at": _now() - timedelta(hours=3),
        "is_read": False,
        "preview": "Please find attached the October Microsoft 365 licence utilisation report. 12 licences are currently unassigned...",
        "body_text": (
            "Hi,\n\n"
            "Please find attached the October Microsoft 365 licence utilisation report. This report is produced monthly for admin review.\n\n"
            "LICENCE SUMMARY — OCTOBER 2026:\n\n"
            "Microsoft 365 Business Premium\n"
            "- Total licences purchased: 120\n"
            "- Active (assigned + last sign-in within 30 days): 104\n"
            "- Assigned but inactive (no sign-in >30 days): 4\n"
            "- Unassigned: 12\n"
            "- Monthly cost per licence: £18.10\n"
            "- Estimated saving if unassigned removed: £217.20/month\n\n"
            "ISSUES IDENTIFIED:\n\n"
            "1. DUPLICATE ASSIGNMENTS (3 users): The following users have been assigned licences under two different accounts. This is likely due to name changes or domain migrations and should be investigated.\n"
            "   - d.walshfinance@contoso.com / d.walsh@contoso.com\n"
            "   - sarah.c@contoso.com / s.connor@contoso.com\n"
            "   - admin.old@contoso.com / admin.user@contoso.com\n\n"
            "2. INACTIVE ACCOUNTS: 4 accounts have not signed in for over 30 days. IT Operations recommends these be reviewed — they may belong to employees who have left but whose accounts have not been deprovisioned.\n\n"
            "3. UNASSIGNED LICENCES: 12 licences are currently unassigned. Before the renewal date on 1st November, please confirm whether additional licences are needed for planned hires. If not, we recommend reducing the licence count at renewal to save costs.\n\n"
            "ACTION REQUIRED BY 31 OCTOBER:\n"
            "- Confirm licence count for renewal\n"
            "- Investigate and resolve duplicate assignments\n"
            "- Deprovision inactive accounts or confirm they are still needed\n\n"
            "Full report attached. Contact IT Operations for any questions.\n\n"
            "IT Operations\nContoso Corporation"
        ),
        "importance": "normal",
    },
    {
        "id": "adm-004",
        "subject": "Backup completed successfully — 2026-03-29",
        "sender_name": "Backup Service",
        "sender_email": "backup@contoso.com",
        "received_at": _now() - timedelta(hours=6),
        "is_read": True,
        "preview": "Nightly backup completed successfully. Duration: 14m 32s. Total size: 48.2 GB. Next scheduled: tomorrow 02:00 UTC...",
        "body_text": (
            "AUTOMATED BACKUP REPORT — 29 March 2026\n\n"
            "Status: COMPLETED SUCCESSFULLY\n\n"
            "BACKUP DETAILS:\n"
            "- Job name: PROD-NIGHTLY-FULL\n"
            "- Start time: 02:00:04 UTC\n"
            "- End time: 02:14:36 UTC\n"
            "- Duration: 14 minutes 32 seconds\n"
            "- Backup type: Full (incremental on weekdays, full on weekends)\n\n"
            "DATA PROTECTED:\n"
            "- Application database (PostgreSQL): 31.4 GB\n"
            "- File storage (Azure Blob): 12.7 GB\n"
            "- Configuration and secrets (encrypted): 0.8 GB\n"
            "- Audit logs: 3.3 GB\n"
            "- Total backup size: 48.2 GB\n\n"
            "VERIFICATION:\n"
            "- Checksum validation: Passed\n"
            "- Restore test (random sample): Passed (3 files sampled)\n"
            "- Encryption: AES-256 applied\n"
            "- Offsite replication: Completed (Azure UK West — secondary region)\n"
            "- Errors: 0\n"
            "- Warnings: 0\n\n"
            "RETENTION:\n"
            "This backup will be retained for 90 days per the current data retention policy. The oldest backup eligible for deletion (28 December 2025) has been purged.\n\n"
            "Next scheduled backup: 30 March 2026 at 02:00 UTC (Sunday — full backup)\n\n"
            "Backup Service\nContoso Corporation Infrastructure\nDo not reply to this email."
        ),
        "importance": "low",
    },
    {
        "id": "adm-005",
        "subject": "New Security Policy — Mandatory Reading",
        "sender_name": "Security Team",
        "sender_email": "security@contoso.com",
        "received_at": _now() - timedelta(hours=5),
        "is_read": True,
        "preview": "A revised information security policy has been issued. All staff must complete the acknowledgement form by Friday...",
        "body_text": (
            "Dear All,\n\n"
            "The Information Security team has published a revised Information Security Policy (v4.2), effective immediately. All employees, including administrators, are required to read the full policy and complete the mandatory acknowledgement form by Friday.\n\n"
            "As system administrator, please note the following changes that are specifically relevant to your role:\n\n"
            "1. PRIVILEGED ACCESS MANAGEMENT: All admin accounts must now use hardware security keys (FIDO2) for MFA — software authenticator apps are no longer accepted for privileged accounts. IT will arrange key distribution this week.\n\n"
            "2. ADMIN ACCOUNT NAMING: Dedicated admin accounts (e.g. admin.user@contoso.com) must not be used for day-to-day activity such as email. Only use admin accounts for administrative tasks. A separate standard user account should be used for daily work.\n\n"
            "3. ACCESS REVIEWS: Quarterly access reviews are now mandatory. As admin, you are responsible for reviewing and certifying all privileged access assignments in your area by the end of each quarter.\n\n"
            "4. CHANGE MANAGEMENT: All changes to production systems must be logged in the ITSM system with a corresponding change request, even for emergency changes. Retrospective logging is no longer acceptable.\n\n"
            "5. LOGGING AND MONITORING: Admin console activity is now logged and reviewed monthly by the Security team. Logs are retained for 12 months.\n\n"
            "Please complete the acknowledgement form at hr.contoso.com/security-acknowledgement by Friday 5pm.\n\n"
            "Information Security Team\nContoso Corporation"
        ),
        "importance": "high",
    },
    {
        "id": "adm-006",
        "subject": "Re: Project Phoenix — Deployment Approval",
        "sender_name": "IT Operations",
        "sender_email": "it.ops@contoso.com",
        "received_at": _now() - timedelta(hours=8),
        "is_read": True,
        "preview": "The change request for Project Phoenix (CR-2847) has been approved by the CAB. Deployment window: Saturday 02:00–06:00 UTC...",
        "body_text": (
            "Hi,\n\n"
            "This is to confirm that Change Request CR-2847 for Project Phoenix Release 3.2.1 has been reviewed and approved by the Change Advisory Board (CAB) at today's 08:30 meeting.\n\n"
            "CHANGE REQUEST DETAILS:\n"
            "- Reference: CR-2847\n"
            "- Change type: Standard (pre-approved category: planned release)\n"
            "- Risk rating: Medium (database schema migration involved)\n"
            "- Approved by CAB: Yes — unanimous approval\n"
            "- Approved by: R. Patel (CAB Chair), A. Morgan (Engineering), D. Walsh (Finance)\n\n"
            "DEPLOYMENT SCHEDULE:\n"
            "- Window: Saturday 29 March 2026, 02:00–06:00 UTC\n"
            "- Maintenance page: Live from 01:45 UTC\n"
            "- Services affected: API (35 min downtime), reporting engine, pipeline scheduler\n"
            "- On-call engineer: T. Hughes (confirmed)\n"
            "- Rollback trigger: If deployment exceeds 3 hours or critical errors exceed threshold\n\n"
            "PRE-DEPLOYMENT SIGN-OFF STATUS:\n"
            "✅ Database migration script — reviewed and approved\n"
            "✅ Load test results — passed\n"
            "✅ Rollback plan — approved\n"
            "✅ Customer communications — sent\n"
            "✅ On-call rota — confirmed\n\n"
            "All pre-deployment items are cleared. You are authorised to proceed with the deployment as scheduled. Please confirm via ITSM (ticket #CHG-2847) once the deployment is complete.\n\n"
            "IT Operations\nContoso Corporation"
        ),
        "importance": "normal",
    },
]

# Fallback — used if user_email doesn't match a known demo role
_MOCK_EMAILS = _MOCK_EMAILS_MANAGER


def _emails_for_user(user_email: str) -> list[dict[str, Any]]:
    """Return the appropriate mock inbox based on the demo user email."""
    name_part = user_email.split("@")[0].lower()
    if "admin" in name_part:
        return _MOCK_EMAILS_ADMIN
    if any(k in name_part for k in ("jamie", "lee", "employee")):
        return _MOCK_EMAILS_EMPLOYEE
    return _MOCK_EMAILS_MANAGER


def _user_category(user_email: str) -> str:
    """Classify a user email into a role category for calendar scoping."""
    name_part = user_email.split("@")[0].lower()
    if "admin" in name_part:
        return "admin"
    if any(k in name_part for k in ("jamie", "lee", "employee")):
        return "employee"
    return "manager"


def _event_visible_to(event: dict[str, Any], user_email: str) -> bool:
    """Return True if this event should appear in user_email's calendar.

    Rules (in priority order):
    1. shared=True events are visible to everyone.
    2. Admin users see everything.
    3. Exact email match on organizer or attendees (voice-created events).
    4. Category match on organizer (seed events — avoids hard-coding demo emails).
    5. Category match on any attendee (invited to a cross-role meeting).
    """
    if event.get("shared"):
        return True

    user_cat = _user_category(user_email)
    if user_cat == "admin":
        return True

    organizer = event.get("organizer", "")
    attendees = event.get("attendees", [])

    # Exact match — handles voice-created events where real JWT email is used
    if organizer == user_email or user_email in attendees:
        return True

    # Category match on organizer — handles seed events
    if _user_category(organizer) == user_cat:
        return True

    # Category match on attendees — e.g. Jamie invited to a manager meeting
    for attendee in attendees:
        if _user_category(attendee) == user_cat:
            return True

    return False

# ---------------------------------------------------------------------------
# Mock calendar data
# ---------------------------------------------------------------------------

_today = _now().replace(hour=0, minute=0, second=0, microsecond=0)

# ---------------------------------------------------------------------------
# Alex Morgan (manager) — personal/management events
# organizer uses "a.morgan@contoso.com" → _user_category → "manager"
# ---------------------------------------------------------------------------
_MOCK_EVENTS: list[dict[str, Any]] = [
    {
        "event_id": "evt-001",
        "subject": "Daily Team Standup",
        "start": (_today + timedelta(hours=9)).isoformat(),
        "end": (_today + timedelta(hours=9, minutes=15)).isoformat(),
        "attendees": [
            "s.connor@contoso.com",
            "j.smith@contoso.com",
            "e.thompson@contoso.com",
            "j.lee@contoso.com",
        ],
        "organizer": "a.morgan@contoso.com",
        "location": "Teams Meeting",
        "description": "Daily sync on blockers and progress.",
        "is_online_meeting": True,
        "meeting_url": "https://teams.microsoft.com/l/meetup/mock-standup",
        "status": "confirmed",
        "shared": True,   # whole team attends — visible to all roles
    },
    {
        "event_id": "evt-002",
        "subject": "Q3 Budget Review with CFO",
        "start": (_today + timedelta(hours=11)).isoformat(),
        "end": (_today + timedelta(hours=12)).isoformat(),
        "attendees": ["cfo@contoso.com", "d.walsh@contoso.com"],
        "organizer": "a.morgan@contoso.com",
        "location": "Board Room A",
        "description": "Review Q3 actuals vs forecast. Prepare slides in advance.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
        # manager-only — not shared
    },
    {
        "event_id": "evt-003",
        "subject": "1-on-1 with Sarah Connor",
        "start": (_today + timedelta(hours=14)).isoformat(),
        "end": (_today + timedelta(hours=14, minutes=30)).isoformat(),
        "attendees": ["s.connor@contoso.com"],
        "organizer": "a.morgan@contoso.com",
        "location": "Room 2C",
        "description": "Regular 1-on-1. Discuss sprint progress and career goals.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
        # manager-only
    },
    {
        "event_id": "evt-004",
        "subject": "Sprint 14 Review",
        "start": (_today + timedelta(days=2, hours=15)).isoformat(),
        "end": (_today + timedelta(days=2, hours=16)).isoformat(),
        "attendees": [
            "s.connor@contoso.com",
            "j.smith@contoso.com",
            "j.lee@contoso.com",
            "e.thompson@contoso.com",
            "product@contoso.com",
        ],
        "organizer": "s.connor@contoso.com",
        "location": "Room 4B",
        "description": "Sprint 14 demo and retrospective. Jamie demoing email summarisation.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
        "shared": True,   # whole team attends
    },
    {
        "event_id": "evt-005",
        "subject": "Board Presentation Prep",
        "start": (_today + timedelta(days=3, hours=10)).isoformat(),
        "end": (_today + timedelta(days=3, hours=11, minutes=30)).isoformat(),
        "attendees": ["d.walsh@contoso.com"],
        "organizer": "a.morgan@contoso.com",
        "location": "Office 5F",
        "description": "Prepare quarterly board presentation materials.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
        # manager-only
    },
    {
        "event_id": "evt-006",
        "subject": "Engineering All-Hands",
        "start": (_today + timedelta(days=4, hours=13)).isoformat(),
        "end": (_today + timedelta(days=4, hours=14)).isoformat(),
        "attendees": ["all-engineering@contoso.com"],
        "organizer": "cto@contoso.com",
        "location": "Main Auditorium",
        "description": "Monthly all-hands for engineering department.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
        "shared": True,   # department-wide
    },
    {
        "event_id": "evt-007",
        "subject": "Acme Corp Client Call — P1 Escalation",
        "start": (_today + timedelta(hours=11, minutes=0)).isoformat(),
        "end": (_today + timedelta(hours=11, minutes=45)).isoformat(),
        "attendees": ["e.thompson@contoso.com", "acme.marcus.reid@acmecorp.com"],
        "organizer": "a.morgan@contoso.com",
        "location": "Teams Meeting",
        "description": "Emergency call with Acme Corp re: data export P1. Authorise service credit if needed.",
        "is_online_meeting": True,
        "meeting_url": "https://teams.microsoft.com/l/meetup/mock-acme",
        "status": "confirmed",
        # manager-only
    },
]

# ---------------------------------------------------------------------------
# Jamie Lee (employee) — personal and team events
# organizer uses "j.lee@contoso.com" → _user_category → "employee" (contains "lee")
# ---------------------------------------------------------------------------
_MOCK_EVENTS_EMPLOYEE: list[dict[str, Any]] = [
    {
        "event_id": "emp-evt-001",
        "subject": "IPA-214 — Graph API Integration (Focus Block)",
        "start": (_today + timedelta(hours=10)).isoformat(),
        "end": (_today + timedelta(hours=12)).isoformat(),
        "attendees": [],
        "organizer": "j.lee@contoso.com",
        "location": "Desk",
        "description": "Focused work block: integrate Microsoft Graph availability endpoint after IPA-211 merge.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
    },
    {
        "event_id": "emp-evt-002",
        "subject": "Pair Programming — Auth Middleware with John",
        "start": (_today + timedelta(days=1, hours=11)).isoformat(),
        "end": (_today + timedelta(days=1, hours=12)).isoformat(),
        "attendees": ["j.smith@contoso.com"],
        "organizer": "j.lee@contoso.com",
        "location": "Teams Meeting",
        "description": "Pair session on IPA-211 OAuth token refresh logic. Review security.py lines 84-112.",
        "is_online_meeting": True,
        "meeting_url": "https://teams.microsoft.com/l/meetup/mock-pair",
        "status": "confirmed",
    },
    {
        "event_id": "emp-evt-003",
        "subject": "1-on-1 with Sarah Connor",
        "start": (_today + timedelta(days=2, hours=10)).isoformat(),
        "end": (_today + timedelta(days=2, hours=10, minutes=30)).isoformat(),
        "attendees": ["s.connor@contoso.com"],
        "organizer": "j.lee@contoso.com",
        "location": "Room 2C",
        "description": "Bi-weekly 1-on-1 with delivery lead. Sprint 14 progress, IPA-214 blocker update.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
    },
    {
        "event_id": "emp-evt-004",
        "subject": "Email Summarisation — Demo Prep",
        "start": (_today + timedelta(days=3, hours=14)).isoformat(),
        "end": (_today + timedelta(days=3, hours=14, minutes=45)).isoformat(),
        "attendees": [],
        "organizer": "j.lee@contoso.com",
        "location": "Desk",
        "description": "Prepare 2-slide summary of email summarisation accuracy for Sprint 14 Review.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
    },
    {
        "event_id": "emp-evt-005",
        "subject": "IPA-219 — Email Service Unit Tests",
        "start": (_today + timedelta(days=4, hours=9)).isoformat(),
        "end": (_today + timedelta(days=4, hours=11)).isoformat(),
        "attendees": [],
        "organizer": "j.lee@contoso.com",
        "location": "Desk",
        "description": "Write unit tests for email summarisation edge cases: null body_text and mixed sentiment.",
        "is_online_meeting": False,
        "meeting_url": "",
        "status": "confirmed",
    },
]


# ---------------------------------------------------------------------------
# Mock Mail Adapter
# ---------------------------------------------------------------------------


class MockGraphMailAdapter:
    """Offline mail adapter — returns hard-coded Contoso mock data."""

    async def get_messages(
        self,
        user_email: str,
        folder: str = "inbox",
        limit: int = 10,
        only_unread: bool = False,
        from_address: str | None = None,
        subject_contains: str | None = None,
        since_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        results = list(_emails_for_user(user_email))

        if only_unread:
            results = [m for m in results if not m["is_read"]]
        if from_address:
            results = [m for m in results if from_address.lower() in m["sender_email"].lower()]
        if subject_contains:
            results = [
                m for m in results if subject_contains.lower() in m["subject"].lower()
            ]

        return results[:limit]

    async def get_message_by_id(self, message_id: str) -> dict[str, Any]:
        all_emails = _MOCK_EMAILS_MANAGER + _MOCK_EMAILS_EMPLOYEE + _MOCK_EMAILS_ADMIN
        for msg in all_emails:
            if msg["id"] == message_id:
                return msg
        raise KeyError(f"Message '{message_id}' not found in mock data.")

    async def send_message(
        self,
        sender_email: str,
        to_recipients: list[str],
        subject: str,
        body: str,
        cc_recipients: list[str] | None = None,
    ) -> str:
        import uuid
        return f"sent-{uuid.uuid4().hex[:8]}"

    async def create_draft(
        self,
        sender_email: str,
        to_recipients: list[str],
        subject: str,
        body: str,
    ) -> str:
        import uuid
        return f"draft-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Mock Calendar Adapter
# ---------------------------------------------------------------------------


class MockGraphCalendarAdapter:
    """Offline calendar adapter — returns hard-coded Contoso mock events."""

    def __init__(self) -> None:
        # Combine all seed events into one list; voice-created events are appended at runtime
        self._events = [dict(e) for e in _MOCK_EVENTS + _MOCK_EVENTS_EMPLOYEE]

    async def get_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """Return events in [start, end] that are visible to user_email.

        Visibility rules are enforced by _event_visible_to():
        - shared events → everyone
        - admin → everything
        - exact email match on organizer/attendees → matched user
        - same role category → same-category users (handles demo email variants)
        """
        results = []
        for event in self._events:
            event_start = datetime.fromisoformat(event["start"])
            if start <= event_start <= end and _event_visible_to(event, user_email):
                results.append(event)
        return results

    async def get_event_by_id(self, event_id: str) -> dict[str, Any]:
        for event in self._events:
            if event["event_id"] == event_id:
                return event
        raise KeyError(f"Event '{event_id}' not found in mock data.")

    async def create_event(
        self,
        user_email: str,
        subject: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
        location: str = "",
        description: str = "",
        is_online_meeting: bool = False,
    ) -> dict[str, Any]:
        import uuid
        new_event = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "subject": subject,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "attendees": attendees,
            "organizer": user_email,
            "location": location,
            "description": description,
            "is_online_meeting": is_online_meeting,
            "meeting_url": "https://teams.microsoft.com/l/meetup/mock-new" if is_online_meeting else "",
            "status": "confirmed",
        }
        self._events.append(new_event)
        return new_event

    async def update_event(
        self,
        event_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        for event in self._events:
            if event["event_id"] == event_id:
                event.update(updates)
                return event
        raise KeyError(f"Event '{event_id}' not found.")

    async def delete_event(self, event_id: str) -> None:
        self._events = [e for e in self._events if e["event_id"] != event_id]

    async def get_free_busy(
        self,
        attendee_emails: list[str],
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        """Return mock free/busy data — all attendees free except during known events."""
        busy_slots = []
        for event in self._events:
            event_start = datetime.fromisoformat(event["start"])
            event_end = datetime.fromisoformat(event["end"])
            if event_start < end and event_end > start:
                for attendee in event.get("attendees", []):
                    if attendee in attendee_emails:
                        busy_slots.append(
                            {"start": event_start.isoformat(), "end": event_end.isoformat(), "email": attendee}
                        )

        return {
            "value": [
                {
                    "scheduleId": email,
                    "availabilityView": "0" * 48,  # simplified: all free
                    "scheduleItems": [
                        slot for slot in busy_slots if slot["email"] == email
                    ],
                }
                for email in attendee_emails
            ]
        }


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

# Module-level singleton instances (one per process — fine for prototype)
_mock_mail = MockGraphMailAdapter()
_mock_calendar = MockGraphCalendarAdapter()


def get_mail_adapter(graph_token: str) -> MockGraphMailAdapter:
    """Return the mock mail adapter regardless of token when USE_MOCK_GRAPH=true."""
    from app.core.config import get_settings
    settings = get_settings()
    if settings.USE_MOCK_GRAPH or not graph_token or graph_token.startswith("mock"):
        return _mock_mail
    # Import live adapter lazily to avoid dependency when not needed
    from app.integrations.graph.mail_adapter import GraphMailAdapter  # noqa: PLC0415
    return GraphMailAdapter(access_token=graph_token)


def get_calendar_adapter(graph_token: str) -> MockGraphCalendarAdapter:
    """Return the mock calendar adapter regardless of token when USE_MOCK_GRAPH=true."""
    from app.core.config import get_settings
    settings = get_settings()
    if settings.USE_MOCK_GRAPH or not graph_token or graph_token.startswith("mock"):
        return _mock_calendar
    from app.integrations.graph.calendar_adapter import GraphCalendarAdapter  # noqa: PLC0415
    return GraphCalendarAdapter(access_token=graph_token)
