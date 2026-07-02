import { useState, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { voiceApi } from '@/services/api/voice'
import type { CommandHistoryEntry, VoiceCommandResponse, VoiceState } from '@/types'
import toast from 'react-hot-toast'

let _historyIdCounter = 0

const CALENDAR_MUTATING_INTENTS = new Set(['create_meeting', 'modify_meeting', 'delete_meeting'])
const CALENDAR_READ_INTENTS = new Set(['list_calendar_events', 'show_employee_calendar', 'check_availability'])

// Web Speech API type declarations (not in all TypeScript environments)
declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition
    webkitSpeechRecognition: new () => SpeechRecognition
  }
}

function getSpeechRecognition(): (new () => SpeechRecognition) | null {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

export const useVoice = () => {
  const queryClient = useQueryClient()
  const [state, setState] = useState<VoiceState>('idle')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState<VoiceCommandResponse | null>(null)
  const [commandHistory, setCommandHistory] = useState<CommandHistoryEntry[]>([])
  const [error, setError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const usingWebSpeechRef = useRef(false)
  const isStartingRef = useRef(false) // prevents double-click race

  const resetError = () => setError(null)

  const speakText = useCallback((text: string, audioBase64?: string) => {
    if (audioBase64 && audioBase64.length > 10) {
      try {
        const bytes = Uint8Array.from(atob(audioBase64), (c) => c.charCodeAt(0))
        const blob = new Blob([bytes], { type: 'audio/mpeg' })
        const url = URL.createObjectURL(blob)
        if (audioRef.current) {
          audioRef.current.src = url
          audioRef.current.play().catch(() => {})
        } else {
          const audio = new Audio(url)
          audioRef.current = audio
          audio.play().catch(() => {})
        }
        return
      } catch {
        // Fall through to browser TTS
      }
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0

      const doSpeak = (voices: SpeechSynthesisVoice[]) => {
        const preferred = voices.find((v) => v.lang.startsWith('en') && v.name.includes('Female'))
          || voices.find((v) => v.lang.startsWith('en'))
        if (preferred) utterance.voice = preferred
        window.speechSynthesis.speak(utterance)
      }

      const voices = window.speechSynthesis.getVoices()
      if (voices.length > 0) {
        doSpeak(voices)
      } else {
        window.speechSynthesis.onvoiceschanged = () => {
          doSpeak(window.speechSynthesis.getVoices())
        }
      }
    }
  }, [])

  const processText = useCallback(async (text: string) => {
    if (!text.trim()) return
    setState('processing')
    setTranscript(text)

    try {
      const result = await voiceApi.processCommand(text)
      setResponse(result)
      setState(result.requires_confirmation ? 'confirming' : 'responding')

      if (!result.requires_confirmation) {
        speakText(result.response_text, result.tts_audio_base64 ?? undefined)
      }

      // Invalidate calendar if a mutating intent completed without confirmation
      if (!result.requires_confirmation && CALENDAR_MUTATING_INTENTS.has(result.intent)) {
        queryClient.invalidateQueries({ queryKey: ['calendar'] })
      }

      setCommandHistory((prev) => [
        {
          id: String(++_historyIdCounter),
          transcript: text,
          intent: result.intent,
          response_text: result.response_text,
          timestamp: new Date(),
          success: !result.clarification_needed,
          requires_confirmation: result.requires_confirmation,
        },
        ...prev.slice(0, 19),
      ])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Command processing failed.'
      setError(msg)
      setState('error')
      toast.error(msg)
    }
  }, [speakText])

  const startRecording = useCallback(async () => {
    // Prevent double-clicks or calls while already active
    if (isStartingRef.current) return
    if (recognitionRef.current) return
    isStartingRef.current = true
    resetError()

    const SpeechRecognitionCtor = getSpeechRecognition()

    // ── Path A: Web Speech API (Chrome / Edge) ──────────────────────────────
    if (SpeechRecognitionCtor) {
      usingWebSpeechRef.current = true

      // Immediate feedback — don't wait for onstart
      setState('recording')

      const recognition = new SpeechRecognitionCtor()
      recognition.lang = 'en-US'
      recognition.continuous = false
      recognition.interimResults = false
      recognition.maxAlternatives = 1

      recognition.onstart = () => {
        isStartingRef.current = false
      }

      recognition.onresult = async (event) => {
        const text = event.results[0][0].transcript.trim()
        if (text) {
          await processText(text)
        }
      }

      recognition.onerror = (event) => {
        recognitionRef.current = null
        usingWebSpeechRef.current = false
        isStartingRef.current = false
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          const msg = 'Microphone access denied. Use the text input below.'
          setError(msg)
          toast.error(msg)
        } else if (event.error === 'no-speech') {
          // User didn't say anything — return to idle silently
        } else {
          const msg = 'Speech recognition failed. Try the text input.'
          setError(msg)
          toast.error(msg)
        }
        setState('idle')
      }

      recognition.onend = () => {
        recognitionRef.current = null
        usingWebSpeechRef.current = false
        isStartingRef.current = false
        setState((prev) => (prev === 'recording' ? 'idle' : prev))
      }

      recognitionRef.current = recognition
      try {
        recognition.start()
      } catch {
        // start() throws if called when another instance is active
        recognitionRef.current = null
        usingWebSpeechRef.current = false
        isStartingRef.current = false
        setState('idle')
      }
      return
    }

    // ── Path B: MediaRecorder → backend STT (fallback for Firefox / Safari) ─
    usingWebSpeechRef.current = false
    isStartingRef.current = false
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/ogg')
          ? 'audio/ogg'
          : ''
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.start(250)
      mediaRecorderRef.current = recorder
      setState('recording')
    } catch {
      const msg = 'Microphone access denied. Use the text input below.'
      setError(msg)
      setState('error')
      toast.error(msg)
    }
  }, [processText])

  const stopRecording = useCallback(async () => {
    // ── Stop Web Speech API ──────────────────────────────────────────────────
    if (usingWebSpeechRef.current && recognitionRef.current) {
      recognitionRef.current.stop()
      return
    }

    // ── Stop MediaRecorder ───────────────────────────────────────────────────
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === 'inactive') return

    setState('processing')
    recorder.stop()
    recorder.stream.getTracks().forEach((t) => t.stop())

    await new Promise<void>((resolve) => {
      recorder.onstop = () => resolve()
    })

    try {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType })
      const arrayBuffer = await blob.arrayBuffer()
      const uint8 = new Uint8Array(arrayBuffer)
      let binary = ''
      uint8.forEach((b) => (binary += String.fromCharCode(b)))
      const base64 = btoa(binary)

      const transcriptionResult = await voiceApi.transcribe(base64, recorder.mimeType)
      const t = transcriptionResult.transcript
      setTranscript(t)
      await processText(t)
    } catch {
      const msg = 'Transcription failed. Please try typing your command.'
      setError(msg)
      setState('error')
      toast.error(msg)
    }
  }, [processText])

  const confirmAction = useCallback(async (confirmed: boolean) => {
    if (!response?.action_id) return
    const pendingIntent = response.intent
    setState('processing')

    try {
      const result = await voiceApi.confirmAction(response.action_id, confirmed)
      setResponse(result)
      setState('responding')
      speakText(result.response_text, result.tts_audio_base64 ?? undefined)
      toast.success(confirmed ? 'Action completed.' : 'Action cancelled.')

      if (confirmed && CALENDAR_MUTATING_INTENTS.has(pendingIntent)) {
        queryClient.invalidateQueries({ queryKey: ['calendar'] })
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Confirmation failed.'
      setError(msg)
      setState('error')
      toast.error(msg)
    }
  }, [response, speakText, queryClient])

  const reset = useCallback(() => {
    setState('idle')
    setTranscript('')
    setResponse(null)
    setError(null)
  }, [])

  return {
    state,
    transcript,
    response,
    commandHistory,
    error,
    startRecording,
    stopRecording,
    processText,
    confirmAction,
    reset,
    speakText,
  }
}
