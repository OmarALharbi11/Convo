"""Pydantic v2 schemas for voice/STT/TTS endpoints."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class TranscriptionRequest(BaseModel):
    audio_data: str  # base64-encoded audio
    language: str = "en-US"
    mime_type: str = "audio/wav"


class TranscriptionResponse(BaseModel):
    transcript: str
    confidence: float = 1.0
    language: str = "en-US"


class VoiceCommandRequest(BaseModel):
    transcript: str
    audio_data: str | None = None  # optional — if provided, transcribe first
    user_context: dict = {}

    @field_validator("transcript")
    @classmethod
    def transcript_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transcript cannot be empty.")
        return v


class VoiceCommandResponse(BaseModel):
    intent: str
    confidence: float
    transcript: str
    response_text: str
    action_result: dict = {}
    tts_audio_base64: str | None = None
    requires_confirmation: bool = False
    action_id: str | None = None  # token for pending confirmation
    clarification_needed: bool = False
    clarification_question: str | None = None
    entities: list[dict] = []  # extracted entities for frontend display


class ConfirmationRequest(BaseModel):
    action_id: str
    confirmed: bool


class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-JennyNeural"
    speed: float = 1.0

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("TTS text cannot be empty.")
        return v

    @field_validator("speed")
    @classmethod
    def valid_speed(cls, v: float) -> float:
        if not 0.5 <= v <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0.")
        return v


class TTSResponse(BaseModel):
    audio_data: str  # base64
    mime_type: str = "audio/mpeg"
    duration_seconds: float = 0.0
