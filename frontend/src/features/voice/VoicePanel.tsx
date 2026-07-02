import { useState, useRef } from 'react'
import { Mic, MicOff, Square, Loader2, Send, Volume2, RotateCcw, CheckCircle, XCircle, User, Calendar, Clock, Timer, Tag, MapPin } from 'lucide-react'
import { clsx } from 'clsx'
import { useVoice } from '@/hooks/useVoice'
import { ConfirmationModal } from '@/components/ui/ConfirmationModal'
import { intentToLabel, getIntentColor, formatRelativeTime } from '@/utils/formatting'
import type { VoiceEntity, VoiceState } from '@/types'

const hasBrowserSTT = typeof window !== 'undefined' &&
  !!(window.SpeechRecognition || (window as any).webkitSpeechRecognition)

const STATE_LABELS: Record<VoiceState, string> = {
  idle: hasBrowserSTT ? 'Tap microphone to speak, or type below' : 'Type a command below (voice not supported in this browser)',
  recording: 'Listening… speak your command, then tap to stop',
  processing: 'Processing command…',
  responding: 'Response ready',
  confirming: 'Confirmation required',
  error: 'Something went wrong',
}

const STATE_COLORS: Record<VoiceState, string> = {
  idle: 'text-slate-400',
  recording: 'text-red-500',
  processing: 'text-brand-500',
  responding: 'text-green-600',
  confirming: 'text-amber-600',
  error: 'text-red-600',
}

// Entity type → display metadata
const ENTITY_META: Record<string, { label: string; icon: typeof User; color: string }> = {
  person: { label: 'Person', icon: User, color: 'bg-blue-50 text-blue-700 border-blue-200' },
  date: { label: 'Date', icon: Calendar, color: 'bg-green-50 text-green-700 border-green-200' },
  time: { label: 'Time', icon: Clock, color: 'bg-purple-50 text-purple-700 border-purple-200' },
  duration: { label: 'Duration', icon: Timer, color: 'bg-orange-50 text-orange-700 border-orange-200' },
  meeting_title: { label: 'Title', icon: Tag, color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
  location: { label: 'Location', icon: MapPin, color: 'bg-teal-50 text-teal-700 border-teal-200' },
  email_subject: { label: 'Subject', icon: Tag, color: 'bg-slate-50 text-slate-700 border-slate-200' },
  email_recipient: { label: 'Recipient', icon: User, color: 'bg-blue-50 text-blue-700 border-blue-200' },
  event_reference: { label: 'Event', icon: Calendar, color: 'bg-amber-50 text-amber-700 border-amber-200' },
  filter_keyword: { label: 'Filter', icon: Tag, color: 'bg-slate-50 text-slate-600 border-slate-200' },
}

function formatDurationMins(value: string): string {
  const mins = parseInt(value, 10)
  if (isNaN(mins)) return value
  if (mins >= 60 && mins % 60 === 0) return `${mins / 60}h`
  if (mins >= 60) return `${Math.floor(mins / 60)}h ${mins % 60}m`
  return `${mins}m`
}

function EntityBadge({ entity }: { entity: VoiceEntity }) {
  const meta = ENTITY_META[entity.type] ?? { label: entity.type, icon: Tag, color: 'bg-slate-50 text-slate-600 border-slate-200' }
  const Icon = meta.icon
  let displayValue = entity.value
  if (entity.type === 'duration') displayValue = formatDurationMins(entity.value)
  else if (entity.type === 'date') {
    try {
      displayValue = new Date(entity.value).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
    } catch { /* keep raw */ }
  }
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border', meta.color)}>
      <Icon size={10} />
      <span className="text-[10px] opacity-70">{meta.label}:</span>
      {displayValue}
    </span>
  )
}

export const VoicePanel = () => {
  const voice = useVoice()
  const [textInput, setTextInput] = useState('')
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const textAreaRef = useRef<HTMLTextAreaElement>(null)

  const isRecording = voice.state === 'recording'
  const isProcessing = voice.state === 'processing'
  const isConfirming = voice.state === 'confirming'
  const disabled = isProcessing

  const handleMicClick = async () => {
    if (isRecording) {
      await voice.stopRecording()
    } else if (!disabled) {
      await voice.startRecording()
    }
  }

  const handleTextSubmit = async () => {
    if (!textInput.trim() || disabled) return
    const text = textInput
    setTextInput('')
    await voice.processText(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleTextSubmit()
    }
  }

  const handleConfirm = async () => {
    setShowConfirmModal(false)
    await voice.confirmAction(true)
  }

  const handleCancel = async () => {
    setShowConfirmModal(false)
    await voice.confirmAction(false)
  }

  const confirmMessage = voice.response?.response_text ?? ''
  const isEmailAction = voice.response?.intent === 'send_email'
  const isDeleteAction = voice.response?.intent === 'delete_meeting'
  const isModifyAction = voice.response?.intent === 'modify_meeting'
  const isCreateAction = voice.response?.intent === 'create_meeting'
  const actionType = isEmailAction ? 'send-email' : isCreateAction ? 'create-meeting' : isDeleteAction ? 'delete-event' : isModifyAction ? 'modify-calendar' : 'generic'

  const visibleEntities = (voice.response?.entities ?? []).filter(
    (e) => e.type !== 'filter_keyword'
  )

  return (
    <div className="flex flex-col gap-4">
      {/* Main voice control */}
      <div className="card p-6">
        <div className="flex flex-col items-center gap-4">
          {/* Status */}
          <p className={clsx('text-sm font-medium', STATE_COLORS[voice.state])}>
            {STATE_LABELS[voice.state]}
          </p>

          {/* Mic button */}
          <button
            onClick={handleMicClick}
            disabled={disabled}
            className={clsx(
              'relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200 shadow-lg',
              isRecording
                ? 'bg-red-500 hover:bg-red-600 animate-pulse-ring'
                : disabled
                  ? 'bg-slate-200 cursor-not-allowed'
                  : 'bg-brand-600 hover:bg-brand-700 hover:shadow-xl active:scale-95',
            )}
            aria-label={isRecording ? 'Stop recording' : 'Start voice command'}
          >
            {isProcessing ? (
              <Loader2 size={28} className="text-white animate-spin" />
            ) : isRecording ? (
              <Square size={24} className="text-white fill-current" />
            ) : (
              <Mic size={28} className="text-white" />
            )}
          </button>

          {/* Intent badge + confidence */}
          {voice.response && voice.state !== 'idle' && (
            <div className="flex items-center gap-2">
              <span className={clsx('px-3 py-1 rounded-full text-xs font-medium', getIntentColor(voice.response.intent))}>
                {intentToLabel(voice.response.intent)}
              </span>
              <span className="text-xs text-slate-400">
                {Math.round(voice.response.confidence * 100)}% confidence
              </span>
            </div>
          )}

          {/* Extracted entities */}
          {visibleEntities.length > 0 && (
            <div className="flex flex-wrap justify-center gap-1.5 max-w-xs">
              {visibleEntities.map((entity, i) => (
                <EntityBadge key={i} entity={entity} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Transcript panel */}
      {voice.transcript && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <Mic size={14} className="text-slate-400" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">You said</span>
          </div>
          <p className="text-sm text-slate-800 font-medium">"{voice.transcript}"</p>
        </div>
      )}

      {/* Response panel */}
      {voice.response && (
        <div className={clsx('card p-4 border-l-4', {
          'border-l-green-500': voice.state === 'responding',
          'border-l-amber-500': isConfirming,
          'border-l-slate-300': voice.state === 'idle',
        })}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Volume2 size={14} className="text-brand-500" />
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Assistant</span>
            </div>
            <button
              onClick={() => voice.speakText(voice.response?.response_text ?? '')}
              className="text-xs text-brand-500 hover:text-brand-700 flex items-center gap-1"
            >
              <Volume2 size={12} /> Replay
            </button>
          </div>
          <p className="text-sm text-slate-800 leading-relaxed">{voice.response.response_text}</p>

          {/* Confirmation actions (inline) */}
          {isConfirming && (
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setShowConfirmModal(true)}
                className="flex items-center gap-1.5 px-4 py-2 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 transition-colors"
              >
                <CheckCircle size={15} /> Confirm
              </button>
              <button
                onClick={handleCancel}
                className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 text-slate-700 text-sm rounded-lg hover:bg-slate-200 transition-colors"
              >
                <XCircle size={15} /> Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {/* Error display */}
      {voice.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
          {voice.error}
        </div>
      )}

      {/* Text fallback input */}
      <div className="card p-4">
        <label className="block text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
          Text Command
        </label>
        <div className="flex gap-2">
          <textarea
            ref={textAreaRef}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder='e.g. "Schedule a meeting with Sarah tomorrow at 2 PM"'
            disabled={disabled}
            rows={2}
            className="input flex-1 resize-none text-sm"
          />
          <button
            onClick={handleTextSubmit}
            disabled={!textInput.trim() || disabled}
            className="btn-primary px-3 self-end"
          >
            <Send size={16} />
          </button>
        </div>
      </div>

      {/* Command history */}
      {voice.commandHistory.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <span className="text-sm font-medium text-slate-700">Recent Commands</span>
            <button onClick={voice.reset} className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1">
              <RotateCcw size={12} /> Clear
            </button>
          </div>
          <div className="divide-y divide-slate-50">
            {voice.commandHistory.slice(0, 5).map((cmd) => (
              <div key={cmd.id} className="px-4 py-3 flex items-start gap-3">
                <span className={clsx('mt-0.5 px-2 py-0.5 rounded text-xs font-medium flex-shrink-0', getIntentColor(cmd.intent))}>
                  {intentToLabel(cmd.intent)}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-slate-600 truncate">"{cmd.transcript}"</p>
                  <p className="text-xs text-slate-400 mt-0.5">{formatRelativeTime(cmd.timestamp.toISOString())}</p>
                </div>
                {cmd.success ? (
                  <CheckCircle size={14} className="text-green-500 mt-0.5 flex-shrink-0" />
                ) : (
                  <XCircle size={14} className="text-slate-400 mt-0.5 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confirmation modal */}
      <ConfirmationModal
        isOpen={showConfirmModal}
        title="Confirm Action"
        message={confirmMessage}
        actionType={actionType}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        autoCloseSeconds={30}
      />
    </div>
  )
}
