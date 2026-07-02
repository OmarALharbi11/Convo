"""
Mock STT provider — cycles through realistic voice commands for testing.

When USE_MOCK_STT=true, audio bytes are ignored and the provider returns
pre-scripted transcripts.  This allows full end-to-end pipeline testing
without microphone hardware or API credentials.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import cycle


class TranscriptionResult:
    def __init__(self, transcript: str, confidence: float = 0.95) -> None:
        self.transcript = transcript
        self.confidence = confidence
        self.language = "en-US"

    def __str__(self) -> str:
        return self.transcript


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mime_type: str = "audio/wav",
    ) -> str:
        """Return the transcribed text string."""


_DEMO_COMMANDS = [
    "Read my latest emails",
    "Summarise my unread emails from this morning",
    "What does my afternoon look like?",
    "Schedule a meeting with Sarah tomorrow at 2 PM",
    "Is the finance team available on Thursday afternoon?",
    "Send an email to David about the Q3 review",
    "What meetings do I have today?",
    "Move my 3 PM meeting to Friday",
    "Check my calendar for this week",
    "Who is available tomorrow morning for a one-hour meeting?",
    "Summarise the email from Emma about the client escalation",
    "Reschedule the budget review to next Monday at 10 AM",
]

_command_cycle = cycle(_DEMO_COMMANDS)


class MockSTTProvider(STTProvider):
    """Returns cycling demo commands regardless of audio input."""

    def __init__(self, fixed_response: str | None = None) -> None:
        self._fixed = fixed_response

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mime_type: str = "audio/wav",
    ) -> str:
        return self._fixed or next(_command_cycle)


class WhisperSTTProvider(STTProvider):
    """OpenAI Whisper-backed STT provider."""

    def __init__(self, api_key: str) -> None:
        import openai
        self._client = openai.AsyncOpenAI(api_key=api_key)

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mime_type: str = "audio/wav",
    ) -> str:
        import tempfile
        import os
        suffix = ".webm" if "webm" in mime_type else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            with open(tmp_path, "rb") as audio_file:
                response = await self._client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language[:2],  # "en-US" → "en"
                )
            return response.text
        finally:
            os.unlink(tmp_path)


def get_stt_provider() -> STTProvider:
    """Factory — returns mock or live provider based on settings."""
    from app.core.config import get_settings
    settings = get_settings()
    if settings.USE_MOCK_STT or not settings.OPENAI_API_KEY:
        return MockSTTProvider()
    return WhisperSTTProvider(api_key=settings.OPENAI_API_KEY)
