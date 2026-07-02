"""
TTS providers — mock (silent WAV), OpenAI, and browser-signal implementations.

The browser provider returns an empty audio payload with a flag indicating
that the frontend should use the Web Speech API (window.speechSynthesis)
instead.  This avoids API costs in development while still exercising the
full voice response pipeline.
"""

from __future__ import annotations

import base64
import struct
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    @abstractmethod
    async def synthesise(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        speed: float = 1.0,
    ) -> bytes:
        """Return raw audio bytes (WAV or MP3)."""


def _silent_wav(duration_ms: int = 200) -> bytes:
    """Generate a minimal valid silent WAV file."""
    sample_rate = 8000
    num_samples = int(sample_rate * duration_ms / 1000)
    data_size = num_samples * 2  # 16-bit mono
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, 1,
        sample_rate, sample_rate * 2, 2, 16,
        b"data", data_size,
    )
    return header + b"\x00" * data_size


class MockTTSProvider(TTSProvider):
    """Returns a silent WAV — no external calls, no audio hardware needed."""

    async def synthesise(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        speed: float = 1.0,
    ) -> bytes:
        return _silent_wav()


class BrowserTTSProvider(TTSProvider):
    """Signals the frontend to use Web Speech API by returning empty bytes.

    Routes check for this by looking at the audio length, or a companion
    flag can be added to the response schema.
    """

    async def synthesise(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        speed: float = 1.0,
    ) -> bytes:
        return b""  # Frontend interprets empty → use speechSynthesis


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS via tts-1 model."""

    def __init__(self, api_key: str) -> None:
        import openai
        self._client = openai.AsyncOpenAI(api_key=api_key)

    async def synthesise(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
    ) -> bytes:
        response = await self._client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text[:4096],  # API limit
            speed=max(0.25, min(4.0, speed)),
        )
        return response.content


def get_tts_provider() -> TTSProvider:
    """Factory — returns appropriate TTS provider based on settings."""
    from app.core.config import get_settings
    settings = get_settings()
    if settings.USE_MOCK_TTS:
        return BrowserTTSProvider()  # Let frontend handle TTS in dev
    if settings.OPENAI_API_KEY:
        return OpenAITTSProvider(api_key=settings.OPENAI_API_KEY)
    return MockTTSProvider()
