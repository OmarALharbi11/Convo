"""
LLM-based intent parser using OpenAI GPT-4o-mini with structured JSON output.

Used as the second tier in HybridIntentClassifier when rule-based confidence
is below threshold.  Failures are caught silently — the rules engine result
is used as fallback.
"""

from __future__ import annotations

import json
import logging

from app.intents.models import ClassifiedIntent, EntityType, ExtractedEntity, Intent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an intent classifier for a corporate voice assistant used by managers.
Classify the user's input into exactly one intent and extract relevant entities.

Supported intents:
- read_emails: user wants to read/check their emails
- summarise_emails: user wants a summary of emails
- send_email: user wants to send or compose an email
- list_calendar_events: user wants to see their calendar/schedule
- check_availability: user wants to check if someone is free
- create_meeting: user wants to schedule a new meeting
- modify_meeting: user wants to reschedule or change a meeting
- delete_meeting: user wants to cancel a meeting
- read_notifications: user wants to hear alerts/reminders
- help: user needs assistance
- repeat_last_response: user wants the last response repeated
- unknown: intent cannot be determined

Entity types to extract:
- person: a person's name
- date: a date reference (resolve to YYYY-MM-DD if possible)
- time: a time reference (resolve to HH:MM 24h if possible)
- duration: a duration in minutes
- email_subject: email subject/topic
- email_recipient: email recipient
- meeting_title: meeting title
- location: a location
- event_reference: reference to an existing meeting/event

Respond ONLY with valid JSON in this exact format:
{
  "intent": "<intent_name>",
  "confidence": <0.0-1.0>,
  "entities": [
    {"type": "<entity_type>", "value": "<normalized_value>", "raw_text": "<original_text>"}
  ],
  "clarification_needed": <true|false>,
  "clarification_question": "<question if needed, else null>"
}"""


class LLMIntentParser:
    def __init__(self, api_key: str) -> None:
        import openai
        self._client = openai.AsyncOpenAI(api_key=api_key)

    async def parse(self, text: str) -> ClassifiedIntent | None:
        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0.1,
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)

            intent_str = data.get("intent", "unknown")
            try:
                intent = Intent(intent_str)
            except ValueError:
                intent = Intent.UNKNOWN

            entities = [
                ExtractedEntity(
                    type=EntityType(e.get("type", "person")),
                    value=e.get("value", ""),
                    raw_text=e.get("raw_text", ""),
                    confidence=0.85,
                )
                for e in data.get("entities", [])
                if e.get("type") in {t.value for t in EntityType}
            ]

            return ClassifiedIntent(
                intent=intent,
                entities=entities,
                confidence=float(data.get("confidence", 0.7)),
                clarification_needed=bool(data.get("clarification_needed", False)),
                clarification_question=data.get("clarification_question"),
                raw_input=text,
                matched_pattern="llm_gpt4o_mini",
            )

        except Exception as exc:
            logger.warning("LLM intent parsing failed: %s", exc)
            return None
