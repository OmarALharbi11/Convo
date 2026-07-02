"""
Voice service — orchestrates the full voice command pipeline.

Pipeline:
  1. Normalise transcript (remove fillers, collapse whitespace)
  2. Classify intent via HybridIntentClassifier
  3a. If clarification needed (or required entities missing) → return question
  3b. If confirmation required → stage action, return confirmation prompt
  3c. Otherwise → execute intent → generate response → synthesise TTS

Confirmation flow uses an in-process dict keyed by UUID action tokens.
In production, move this to Redis or a DB-backed session store.
"""

from __future__ import annotations

import base64
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.intents.models import ClassifiedIntent, EntityType, Intent
from app.schemas.calendar import CreateEventRequest, UpdateEventRequest
from app.schemas.email import EmailFilter, SendEmailRequest
from app.schemas.voice import ConfirmationRequest, VoiceCommandRequest, VoiceCommandResponse

# ---------------------------------------------------------------------------
# Pending action store  (token → {intent, user_context, expires_at})
# ---------------------------------------------------------------------------
_PENDING_ACTIONS: dict[str, dict[str, Any]] = {}
_ACTION_TTL_SECONDS = 120  # 2 minutes to confirm

# ---------------------------------------------------------------------------
# Transcript normalisation
# ---------------------------------------------------------------------------
_FILLER_RE = re.compile(
    r"\b(um+|uh+|er+|ah+|hmm+|okay so|you know|i mean|basically|actually|so)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    """Remove filler words and collapse extra whitespace."""
    text = _FILLER_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# VoiceService
# ---------------------------------------------------------------------------


class VoiceService:
    def __init__(
        self,
        stt_provider,
        tts_provider,
        classifier,
        email_service,
        calendar_service,
    ) -> None:
        self._stt = stt_provider
        self._tts = tts_provider
        self._classifier = classifier
        self._email = email_service
        self._calendar = calendar_service

    # ------------------------------------------------------------------
    # Main command processing
    # ------------------------------------------------------------------

    async def process_command(
        self,
        request: VoiceCommandRequest,
        user_context: dict[str, Any],
    ) -> VoiceCommandResponse:
        raw_transcript = request.transcript.strip()
        transcript = _normalize(raw_transcript)

        # Classify intent
        intent_result: ClassifiedIntent = await self._classifier.classify(transcript)
        entities_json = [e.model_dump(mode="json") for e in intent_result.entities]

        # Step A: Clarification needed (unknown or low-confidence or flagged)
        if intent_result.clarification_needed or intent_result.intent == Intent.UNKNOWN:
            response_text = (
                intent_result.clarification_question
                or "I didn't understand that. Try: 'Read my emails', 'What's on my calendar?', or say 'help'."
            )
            return VoiceCommandResponse(
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
                transcript=raw_transcript,
                response_text=response_text,
                clarification_needed=True,
                clarification_question=intent_result.clarification_question,
                tts_audio_base64=await self._tts_encode(response_text),
                entities=entities_json,
            )

        # Step B: Check for missing required entities before confirmation
        missing_question = self._check_missing_entities(intent_result)
        if missing_question:
            return VoiceCommandResponse(
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
                transcript=raw_transcript,
                response_text=missing_question,
                clarification_needed=True,
                clarification_question=missing_question,
                tts_audio_base64=await self._tts_encode(missing_question),
                entities=entities_json,
            )

        # Step C: Confirmation required for risky actions
        if intent_result.requires_confirmation:
            action_id = str(uuid.uuid4())
            _PENDING_ACTIONS[action_id] = {
                "intent": intent_result,
                "user_context": user_context,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=_ACTION_TTL_SECONDS),
            }
            response_text = self._build_confirmation_prompt(intent_result)
            return VoiceCommandResponse(
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
                transcript=raw_transcript,
                response_text=response_text,
                requires_confirmation=True,
                action_id=action_id,
                tts_audio_base64=await self._tts_encode(response_text),
                entities=entities_json,
            )

        # Step D: Execute immediately
        action_result = await self._execute_intent(intent_result, user_context)
        response_text = self._format_response(intent_result.intent, action_result)
        return VoiceCommandResponse(
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            transcript=raw_transcript,
            response_text=response_text,
            action_result=action_result,
            tts_audio_base64=await self._tts_encode(response_text),
            entities=entities_json,
        )

    # ------------------------------------------------------------------
    # Confirmation flow
    # ------------------------------------------------------------------

    async def confirm_action(
        self,
        request: ConfirmationRequest,
        user_context: dict[str, Any],
    ) -> VoiceCommandResponse:
        pending = _PENDING_ACTIONS.pop(request.action_id, None)

        if pending is None:
            msg = "This action has expired or was already processed. Please try again."
            return VoiceCommandResponse(
                intent="unknown", confidence=0.0, transcript="",
                response_text=msg, tts_audio_base64=await self._tts_encode(msg),
            )

        if datetime.now(timezone.utc) > pending["expires_at"]:
            msg = "This action timed out. Please repeat your command."
            return VoiceCommandResponse(
                intent="unknown", confidence=0.0, transcript="",
                response_text=msg, tts_audio_base64=await self._tts_encode(msg),
            )

        if not request.confirmed:
            msg = "Action cancelled. No changes were made."
            return VoiceCommandResponse(
                intent=pending["intent"].intent.value,
                confidence=pending["intent"].confidence,
                transcript="",
                response_text=msg,
                tts_audio_base64=await self._tts_encode(msg),
            )

        intent_result: ClassifiedIntent = pending["intent"]
        action_result = await self._execute_intent(intent_result, user_context)
        response_text = self._format_response(intent_result.intent, action_result)
        return VoiceCommandResponse(
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            transcript="",
            response_text=response_text,
            action_result=action_result,
            tts_audio_base64=await self._tts_encode(response_text),
            entities=[e.model_dump(mode="json") for e in intent_result.entities],
        )

    # ------------------------------------------------------------------
    # Entity validation (clarification before confirmation)
    # ------------------------------------------------------------------

    @staticmethod
    def _check_missing_entities(intent: ClassifiedIntent) -> str | None:
        """Return a clarification question if required entities are absent."""
        entities = {e.type.value: e.value for e in intent.entities}

        if intent.intent == Intent.SEND_EMAIL:
            recipient = entities.get(EntityType.EMAIL_RECIPIENT.value) or entities.get(EntityType.PERSON.value, "")
            if not recipient.strip():
                return "Who should I send this email to? Please provide a name or email address."

        if intent.intent == Intent.CREATE_MEETING:
            # A meeting needs at minimum a date or time to schedule.
            # Person is optional — the user can create solo or titled meetings.
            date_val = entities.get(EntityType.DATE.value, "")
            time_val = entities.get(EntityType.TIME.value, "")
            if not date_val and not time_val:
                return "When should I schedule this meeting? Please say a date and time, for example 'tomorrow at 2 PM'."

        if intent.intent == Intent.MODIFY_MEETING:
            date_val = entities.get(EntityType.DATE.value, "")
            time_val = entities.get(EntityType.TIME.value, "")
            if not date_val and not time_val:
                return "When should I move this meeting to? Please specify a date or time."

        if intent.intent == Intent.SHOW_EMPLOYEE_CALENDAR:
            person = entities.get(EntityType.PERSON.value, "")
            if not person.strip():
                return "Whose calendar should I show? Please say their name."

        return None

    # ------------------------------------------------------------------
    # Intent execution
    # ------------------------------------------------------------------

    async def _execute_intent(
        self, intent: ClassifiedIntent, user_context: dict[str, Any]
    ) -> dict[str, Any]:
        user_email = user_context.get("email", "user@unknown.com")
        entities = {e.type.value: e.value for e in intent.entities}
        now = datetime.now(timezone.utc)

        # --- Read emails ---
        if intent.intent == Intent.READ_EMAILS:
            only_unread = "unread" in intent.raw_input.lower()
            result = await self._email.get_inbox(
                user_email=user_email,
                email_filter=EmailFilter(limit=5, only_unread=only_unread),
            )
            return {"messages": [m.model_dump(mode="json") for m in result.messages]}

        # --- Summarise emails ---
        if intent.intent == Intent.SUMMARISE_EMAILS:
            summaries = await self._email.summarise_recent(user_email=user_email, count=5)
            return {"summaries": [s.model_dump(mode="json") for s in summaries]}

        # --- Send email ---
        if intent.intent == Intent.SEND_EMAIL:
            recipient = entities.get(EntityType.EMAIL_RECIPIENT.value) or entities.get(EntityType.PERSON.value, "")
            subject = entities.get(EntityType.EMAIL_SUBJECT.value, "Message from Convo")
            # Resolve name → email if no @ present
            if "@" not in recipient:
                recipient = f"{recipient.lower().replace(' ', '.')}@contoso.com"
            req = SendEmailRequest(
                to=[recipient],
                subject=subject,
                body=f"[Composed via Convo voice command]\n\nSubject: {subject}",
            )
            result = await self._email.send_email(sender_email=user_email, request=req)
            return {"message_id": result.message_id, "status": result.status}

        # --- List calendar events ---
        if intent.intent == Intent.LIST_CALENDAR_EVENTS:
            raw_lower = intent.raw_input.lower()
            if "week" in raw_lower or "week" in entities.get(EntityType.DATE.value, ""):
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=7)
            else:
                date_str = entities.get(EntityType.DATE.value, "")
                target_date = self._resolve_date(date_str) if date_str else now.date()
                start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
                end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=timezone.utc)
            result = await self._calendar.get_events(user_email=user_email, start=start, end=end)
            return {"events": [e.model_dump(mode="json") for e in result.events], "is_week": "week" in intent.raw_input.lower()}

        # --- Check availability ---
        if intent.intent == Intent.CHECK_AVAILABILITY:
            from app.schemas.calendar import AvailabilityRequest
            person = entities.get(EntityType.PERSON.value, "")
            email_addr = person if "@" in person else f"{person.lower().replace(' ', '.')}@contoso.com"
            req = AvailabilityRequest(
                attendee_emails=[email_addr],
                start=now,
                end=now + timedelta(hours=8),
                duration_minutes=30,
            )
            result = await self._calendar.check_availability(requester_email=user_email, request=req)
            return {
                "slots": [s.model_dump(mode="json") for s in result.slots[:6]],
                "suggested": [s.model_dump(mode="json") for s in result.suggested_times],
                "person": person,
            }

        # --- Create meeting ---
        if intent.intent == Intent.CREATE_MEETING:
            person = entities.get(EntityType.PERSON.value, "")
            date_str = entities.get(EntityType.DATE.value, "")
            time_str = entities.get(EntityType.TIME.value, "09:00")
            duration_mins = int(entities.get(EntityType.DURATION.value, "60"))
            subject = entities.get(EntityType.MEETING_TITLE.value) or (f"Meeting with {person}" if person else "New Meeting")
            location = entities.get(EntityType.LOCATION.value, "")
            start_dt = self._build_datetime(date_str, time_str)
            end_dt = start_dt + timedelta(minutes=duration_mins)
            attendees = [f"{person.lower().replace(' ', '.')}@contoso.com"] if person else []
            req = CreateEventRequest(
                subject=subject,
                start=start_dt,
                end=end_dt,
                attendees=attendees,
                location=location,
                is_online_meeting=not location,
            )
            event = await self._calendar.create_event(user_email=user_email, request=req)
            return {"event": event.model_dump(mode="json")}

        # --- Modify meeting ---
        if intent.intent == Intent.MODIFY_MEETING:
            event_ref = entities.get(EntityType.EVENT_REFERENCE.value, "")
            date_str = entities.get(EntityType.DATE.value, "")
            time_str = entities.get(EntityType.TIME.value, "")

            # Find the target event
            target_event = await self._find_event_by_ref(user_email, event_ref)
            if target_event is None:
                return {"error": "I couldn't find a matching meeting. Please be more specific."}

            new_start = self._build_datetime(date_str, time_str) if (date_str or time_str) else None
            new_end = (new_start + timedelta(hours=1)) if new_start else None
            req = UpdateEventRequest(start=new_start, end=new_end)
            updated = await self._calendar.update_event(
                user_email=user_email,
                event_id=target_event["event_id"],
                request=req,
            )
            return {"event": updated.model_dump(mode="json")}

        # --- Delete meeting ---
        if intent.intent == Intent.DELETE_MEETING:
            event_ref = entities.get(EntityType.EVENT_REFERENCE.value, "")
            target_event = await self._find_event_by_ref(user_email, event_ref)
            if target_event is None:
                return {"error": "I couldn't find a matching meeting to cancel."}
            await self._calendar.delete_event(user_email=user_email, event_id=target_event["event_id"])
            return {"deleted": True, "subject": target_event["subject"]}

        # --- Show employee calendar ---
        if intent.intent == Intent.SHOW_EMPLOYEE_CALENDAR:
            person = entities.get(EntityType.PERSON.value, "")
            employee_email = person if "@" in person else f"{person.lower().replace(' ', '.')}@contoso.com"
            date_str = entities.get(EntityType.DATE.value, "")
            target_date = self._resolve_date(date_str) if date_str else now.date()
            # Show a week's worth if no specific date, else just that day
            if date_str:
                start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, tzinfo=timezone.utc)
                end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, tzinfo=timezone.utc)
            else:
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=7)
            result = await self._calendar.get_events(user_email=employee_email, start=start, end=end)
            return {
                "events": [e.model_dump(mode="json") for e in result.events],
                "person": person,
                "employee_email": employee_email,
            }

        # --- Help ---
        if intent.intent == Intent.HELP:
            return {
                "commands": [
                    "Read my emails",
                    "Summarise my unread emails",
                    "What's on my calendar today?",
                    "What meetings do I have this week?",
                    "Schedule a meeting with [Name] tomorrow at 2 PM",
                    "Is [Name] available tomorrow?",
                    "Send an email to [Name] about [topic]",
                    "Cancel my [meeting name]",
                    "Move my [meeting] to Friday at 3 PM",
                ]
            }

        if intent.intent == Intent.REPEAT_LAST:
            return {"note": "repeat"}

        if intent.intent == Intent.READ_NOTIFICATIONS:
            return {"note": "No new notifications at this time."}

        return {"note": f"No handler for intent: {intent.intent.value}"}

    # ------------------------------------------------------------------
    # Natural language response formatting
    # ------------------------------------------------------------------

    def _format_response(self, intent: Intent, result: dict[str, Any]) -> str:
        if "error" in result:
            return result["error"]

        if intent == Intent.READ_EMAILS:
            messages = result.get("messages", [])
            if not messages:
                return "You have no emails in your inbox."
            unread = [m for m in messages if not m.get("is_read", True)]
            total = len(messages)
            response = f"You have {total} email{'s' if total != 1 else ''} in your inbox"
            if unread:
                response += f", {len(unread)} unread"
            first = messages[0]
            response += f". The most recent is from {first.get('sender_name', 'someone')} — {first.get('subject', 'no subject')}."
            return response

        if intent == Intent.SUMMARISE_EMAILS:
            summaries = result.get("summaries", [])
            if not summaries:
                return "No recent emails to summarise."
            urgent = [s for s in summaries if s.get("urgency_level") == "high"]
            response = f"I've summarised your {len(summaries)} most recent emails."
            if urgent:
                response += f" {len(urgent)} need{'s' if len(urgent) == 1 else ''} urgent attention."
                response += f" Highest priority: {urgent[0].get('subject', 'unknown')}."
            return response

        if intent == Intent.SEND_EMAIL:
            return "Email sent successfully."

        if intent == Intent.LIST_CALENDAR_EVENTS:
            events = result.get("events", [])
            is_week = result.get("is_week", False)
            period = "this week" if is_week else "today"
            if not events:
                return f"You have no meetings {period}."
            response = f"You have {len(events)} meeting{'s' if len(events) != 1 else ''} {period}."
            if events:
                first = events[0]
                try:
                    start_time = datetime.fromisoformat(first["start"]).strftime("%I:%M %p").lstrip("0")
                except Exception:
                    start_time = "soon"
                response += f" Next up: {first.get('subject', 'untitled')} at {start_time}."
            return response

        if intent == Intent.CHECK_AVAILABILITY:
            suggested = result.get("suggested", [])
            person = result.get("person", "them")
            if not suggested:
                return f"I couldn't find a free slot for {person} in the next 8 hours."
            first = suggested[0]
            try:
                start_time = datetime.fromisoformat(first["start"]).strftime("%I:%M %p").lstrip("0")
                return f"The earliest available slot is at {start_time}."
            except Exception:
                return f"Found {len(suggested)} available time slot{'s' if len(suggested) != 1 else ''}."

        if intent == Intent.CREATE_MEETING:
            event = result.get("event", {})
            subject = event.get("subject", "the meeting")
            try:
                start_time = datetime.fromisoformat(event["start"]).strftime("%A at %I:%M %p")
            except Exception:
                start_time = "the requested time"
            return f"Done. '{subject}' has been scheduled for {start_time}."

        if intent == Intent.MODIFY_MEETING:
            event = result.get("event", {})
            subject = event.get("subject", "the meeting")
            try:
                start_time = datetime.fromisoformat(event["start"]).strftime("%A at %I:%M %p")
            except Exception:
                start_time = "the new time"
            return f"Done. '{subject}' has been moved to {start_time}."

        if intent == Intent.DELETE_MEETING:
            subject = result.get("subject", "the meeting")
            return f"Done. '{subject}' has been cancelled."

        if intent == Intent.SHOW_EMPLOYEE_CALENDAR:
            events = result.get("events", [])
            person = result.get("person", "them")
            if not events:
                return f"{person}'s calendar is clear — no meetings found."
            count = len(events)
            response = f"{person} has {count} meeting{'s' if count != 1 else ''}."
            first = events[0]
            try:
                start_time = datetime.fromisoformat(first["start"]).strftime("%A at %I:%M %p").lstrip("0")
                response += f" Next: {first.get('subject', 'untitled')} on {start_time}."
            except Exception:
                pass
            return response

        if intent == Intent.HELP:
            commands = result.get("commands", [])
            return "I can help with: " + ", ".join(commands[:4]) + ", and more. Just speak or type your request."

        if intent == Intent.READ_NOTIFICATIONS:
            return result.get("note", "No new notifications.")

        return "Done."

    # ------------------------------------------------------------------
    # Confirmation prompt builder
    # ------------------------------------------------------------------

    def _build_confirmation_prompt(self, intent: ClassifiedIntent) -> str:
        entities = {e.type.value: e.value for e in intent.entities}

        if intent.intent == Intent.SEND_EMAIL:
            recipient = entities.get(EntityType.EMAIL_RECIPIENT.value) or entities.get(EntityType.PERSON.value, "the recipient")
            subject = entities.get(EntityType.EMAIL_SUBJECT.value, "this topic")
            return f"I'll send an email to {recipient} about {subject}. Confirm to send, or cancel to abort."

        if intent.intent == Intent.CREATE_MEETING:
            person = entities.get(EntityType.PERSON.value, "")
            title = entities.get(EntityType.MEETING_TITLE.value, "")
            subject = title or (f"Meeting with {person}" if person else "New Meeting")
            date_ref = entities.get(EntityType.DATE.value, "")
            time_ref = entities.get(EntityType.TIME.value, "09:00")
            duration = entities.get(EntityType.DURATION.value, "60")
            # Format friendly date
            try:
                from datetime import date as date_type
                d = date_type.fromisoformat(date_ref) if date_ref else (date_type.today() + timedelta(days=1))
                date_label = d.strftime("%A %d %B")
            except Exception:
                date_label = date_ref or "tomorrow"
            with_part = f" with {person}" if person else ""
            return (
                f"I'll create '{subject}'{with_part} on {date_label} at {time_ref} "
                f"for {duration} minutes. Confirm to schedule, or cancel."
            )

        if intent.intent == Intent.MODIFY_MEETING:
            event_ref = entities.get(EntityType.EVENT_REFERENCE.value, "the meeting")
            date_ref = entities.get(EntityType.DATE.value, "")
            time_ref = entities.get(EntityType.TIME.value, "")
            when = f"{date_ref} at {time_ref}".strip(" at") if (date_ref or time_ref) else "the new time"
            return f"I'll reschedule '{event_ref}' to {when}. Confirm to proceed, or cancel."

        if intent.intent == Intent.DELETE_MEETING:
            event_ref = entities.get(EntityType.EVENT_REFERENCE.value, "the meeting")
            return f"I'll cancel '{event_ref}'. This cannot be undone. Confirm to proceed, or cancel."

        return f"Confirm the '{intent.intent.value}' action, or cancel."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _find_event_by_ref(self, user_email: str, event_ref: str) -> dict[str, Any] | None:
        """Search the next 7 days of events for one matching event_ref."""
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        events_result = await self._calendar.get_events(user_email=user_email, start=start, end=end)

        if not events_result.events:
            return None

        if event_ref:
            ref_lower = event_ref.lower()
            for ev in events_result.events:
                if ref_lower in ev.subject.lower():
                    return ev.model_dump(mode="json")

        # Fall back to the next upcoming event
        return events_result.events[0].model_dump(mode="json")

    async def _tts_encode(self, text: str) -> str | None:
        """Synthesise text and return base64, or None to signal browser TTS."""
        try:
            audio_bytes = await self._tts.synthesise(text)
            if not audio_bytes:
                return None
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            return None

    @staticmethod
    def _build_datetime(date_str: str, time_str: str) -> datetime:
        from datetime import date as date_type
        now = datetime.now(timezone.utc)
        try:
            d = datetime.fromisoformat(date_str).date() if date_str else (now + timedelta(days=1)).date()
        except ValueError:
            d = (now + timedelta(days=1)).date()
        try:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError):
            hour, minute = 9, 0
        return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)

    @staticmethod
    def _resolve_date(date_str: str):
        from datetime import date
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            return date.today()
