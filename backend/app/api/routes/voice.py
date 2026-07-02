"""Voice router — STT, command processing, confirmation, TTS, diagnostics."""

from __future__ import annotations

import base64
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.security import get_current_user
from app.integrations.graph.mock_adapter import get_calendar_adapter, get_mail_adapter
from app.integrations.stt.mock_provider import get_stt_provider
from app.integrations.tts.mock_provider import get_tts_provider
from app.intents.classifier import get_classifier
from app.schemas.voice import (
    ConfirmationRequest,
    TranscriptionRequest,
    TranscriptionResponse,
    TTSRequest,
    TTSResponse,
    VoiceCommandRequest,
    VoiceCommandResponse,
)
from app.services.calendar_service import CalendarService
from app.services.email_service import EmailService
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice"])


def _build_voice_service(current_user: dict) -> VoiceService:
    token = current_user.get("graph_access_token", "mock")
    return VoiceService(
        stt_provider=get_stt_provider(),
        tts_provider=get_tts_provider(),
        classifier=get_classifier(),
        email_service=EmailService(mail_adapter=get_mail_adapter(graph_token=token)),
        calendar_service=CalendarService(calendar_adapter=get_calendar_adapter(graph_token=token)),
    )


def _user_context(current_user: dict) -> dict:
    return {
        "user_id": current_user["sub"],
        "email": current_user.get("email", ""),
        "display_name": current_user.get("display_name", ""),
        "role": current_user.get("role", "employee"),
    }


@router.post("/transcribe", response_model=TranscriptionResponse, summary="Transcribe audio to text")
async def transcribe_audio(
    request: TranscriptionRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> TranscriptionResponse:
    audit_logger = get_audit_logger()
    try:
        audio_bytes = base64.b64decode(request.audio_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 audio: {exc}") from exc

    stt = get_stt_provider()
    transcript = await stt.transcribe(audio_bytes=audio_bytes, language=request.language, mime_type=request.mime_type)

    await audit_logger.log(AuditAction.VOICE_COMMAND, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"action": "transcribe"})
    return TranscriptionResponse(transcript=str(transcript), language=request.language)


@router.post("/command", response_model=VoiceCommandResponse, summary="Process voice command")
async def process_voice_command(
    request: VoiceCommandRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> VoiceCommandResponse:
    audit_logger = get_audit_logger()
    voice_service = _build_voice_service(current_user)

    try:
        response = await voice_service.process_command(
            request=request,
            user_context=_user_context(current_user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Voice command processing error")
        raise HTTPException(status_code=500, detail=f"Command processing failed: {exc}") from exc

    await audit_logger.log(AuditAction.INTENT_CLASSIFIED, actor_id=current_user["sub"],
                           actor_email=current_user.get("email", ""),
                           actor_role=current_user.get("role", ""),
                           details={"intent": response.intent, "confidence": response.confidence,
                                    "transcript": request.transcript})
    return response


@router.post("/confirm", response_model=VoiceCommandResponse, summary="Confirm or cancel pending action")
async def confirm_action(
    request: ConfirmationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> VoiceCommandResponse:
    voice_service = _build_voice_service(current_user)
    return await voice_service.confirm_action(
        request=request,
        user_context=_user_context(current_user),
    )


@router.post("/tts", response_model=TTSResponse, summary="Text to speech")
async def text_to_speech(
    request: TTSRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> TTSResponse:
    tts = get_tts_provider()
    audio_bytes = await tts.synthesise(text=request.text, voice=request.voice, speed=request.speed)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""
    return TTSResponse(audio_data=audio_b64, mime_type="audio/mpeg")


@router.get("/intent-diagnostics", summary="[Admin] Last intent classification debug info")
async def get_intent_diagnostics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    classifier = get_classifier()
    return {
        "classifier_type": type(classifier).__name__,
        "last_classification": classifier.get_last_debug_info(),
        "supported_intents": classifier.supported_intents,
    }
