"""Voice command pipeline integration tests."""

from __future__ import annotations

import base64
import pytest


_SILENT_WAV_B64 = base64.b64encode(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00").decode()


class TestVoiceRoutes:
    @pytest.mark.asyncio
    async def test_transcribe_endpoint(self, manager_client):
        resp = await manager_client.post("/api/voice/transcribe", json={
            "audio_data": _SILENT_WAV_B64,
            "language": "en-US",
            "mime_type": "audio/wav",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "transcript" in data
        assert len(data["transcript"]) > 0  # Mock returns a cycling command

    @pytest.mark.asyncio
    async def test_voice_command_read_emails(self, manager_client):
        resp = await manager_client.post("/api/voice/command", json={
            "transcript": "Read my latest emails"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "read_emails"
        assert data["confidence"] > 0.5
        assert len(data["response_text"]) > 0

    @pytest.mark.asyncio
    async def test_voice_command_returns_response_text(self, manager_client):
        resp = await manager_client.post("/api/voice/command", json={
            "transcript": "What do I have today?"
        })
        assert resp.status_code == 200
        assert len(resp.json()["response_text"]) > 0

    @pytest.mark.asyncio
    async def test_voice_command_send_email_requires_confirmation(self, manager_client):
        resp = await manager_client.post("/api/voice/command", json={
            "transcript": "Send an email to David about the Q3 review"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "send_email"
        assert data["requires_confirmation"] is True
        assert data["action_id"] is not None

    @pytest.mark.asyncio
    async def test_voice_command_confirm_action(self, manager_client):
        # Step 1: Trigger send email (gets confirmation token)
        cmd_resp = await manager_client.post("/api/voice/command", json={
            "transcript": "Send an email to Sarah about the project"
        })
        assert cmd_resp.status_code == 200
        action_id = cmd_resp.json().get("action_id")
        assert action_id is not None

        # Step 2: Confirm the action
        confirm_resp = await manager_client.post("/api/voice/confirm", json={
            "action_id": action_id,
            "confirmed": True,
        })
        assert confirm_resp.status_code == 200
        assert "sent" in confirm_resp.json()["response_text"].lower() or \
               confirm_resp.json()["intent"] == "send_email"

    @pytest.mark.asyncio
    async def test_voice_command_cancel_action(self, manager_client):
        cmd_resp = await manager_client.post("/api/voice/command", json={
            "transcript": "Cancel my standup tomorrow"
        })
        if cmd_resp.json().get("requires_confirmation"):
            action_id = cmd_resp.json()["action_id"]
            cancel_resp = await manager_client.post("/api/voice/confirm", json={
                "action_id": action_id,
                "confirmed": False,
            })
            assert cancel_resp.status_code == 200
            assert "cancel" in cancel_resp.json()["response_text"].lower()

    @pytest.mark.asyncio
    async def test_voice_command_unknown_triggers_clarification(self, manager_client):
        resp = await manager_client.post("/api/voice/command", json={
            "transcript": "xyzzy plugh frobozz magic words"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "unknown"
        assert data["clarification_needed"] is True

    @pytest.mark.asyncio
    async def test_tts_endpoint_returns_audio(self, manager_client):
        resp = await manager_client.post("/api/voice/tts", json={
            "text": "Hello, this is a test response from IPA."
        })
        assert resp.status_code == 200
        assert "audio_data" in resp.json()

    @pytest.mark.asyncio
    async def test_empty_transcript_returns_422(self, manager_client):
        resp = await manager_client.post("/api/voice/command", json={"transcript": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_intent_diagnostics(self, manager_client):
        # First run a command so diagnostics have data
        await manager_client.post("/api/voice/command", json={"transcript": "Check my inbox"})
        resp = await manager_client.get("/api/voice/intent-diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert "classifier_type" in data
        assert "supported_intents" in data
