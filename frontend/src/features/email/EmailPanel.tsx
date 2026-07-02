import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Mail, RefreshCw, Filter, Loader2, AlertCircle, Volume2, VolumeX, Star } from 'lucide-react'
import { clsx } from 'clsx'
import { emailApi } from '@/services/api/email'
import { formatRelativeTime, truncate, getImportanceColor } from '@/utils/formatting'
import { ComposeModal } from './ComposeModal'
import { EmailSummaryCard } from './EmailSummaryCard'
import type { EmailMessage } from '@/types'
import toast from 'react-hot-toast'

interface EmailPanelProps {
  onReadAloud?: (text: string) => void
}

export const EmailPanel = ({ onReadAloud }: EmailPanelProps) => {
  const [onlyUnread, setOnlyUnread] = useState(false)
  const [selectedMessage, setSelectedMessage] = useState<EmailMessage | null>(null)
  const [showCompose, setShowCompose] = useState(false)
  const [summaryId, setSummaryId] = useState<string | null>(null)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  // Cancel speech when switching emails or unmounting
  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel()
      setIsSpeaking(false)
    }
  }, [selectedMessage?.id])

  useEffect(() => {
    return () => { window.speechSynthesis?.cancel() }
  }, [])

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['inbox', onlyUnread],
    queryFn: () => emailApi.getInbox({ limit: 15, only_unread: onlyUnread }),
  })

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['email-summary', summaryId],
    queryFn: () => emailApi.summariseMessage(summaryId!),
    enabled: !!summaryId,
  })

  const messages = data?.messages ?? []

  const handleStopReading = () => {
    window.speechSynthesis.cancel()
    utteranceRef.current = null
    setIsSpeaking(false)
  }

  const speakText = (text: string) => {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    setIsSpeaking(false)

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.0
    utterance.pitch = 1.0
    utterance.volume = 1.0
    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => { setIsSpeaking(false); utteranceRef.current = null }
    utterance.onerror = () => { setIsSpeaking(false); utteranceRef.current = null }
    utteranceRef.current = utterance

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
      // onvoiceschanged fires once — detach after first call to prevent duplicate speaks
      const onReady = () => {
        window.speechSynthesis.onvoiceschanged = null
        doSpeak(window.speechSynthesis.getVoices())
      }
      window.speechSynthesis.onvoiceschanged = onReady
    }
  }

  const handleReadAloud = (msg: EmailMessage) => {
    const text = `Email from ${msg.sender_name}. Subject: ${msg.subject}. ${msg.body_text ?? msg.preview}`
    if (onReadAloud) {
      onReadAloud(text)
    } else {
      speakText(text)
    }
  }

  const handleReadSummary = (summaryText: string) => {
    speakText(summaryText)
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Email list */}
      <div className="flex flex-col gap-3">
        {/* Toolbar */}
        <div className="card p-3 flex items-center gap-3">
          <h2 className="text-sm font-semibold text-slate-700 flex-1">Inbox</h2>
          <button
            onClick={() => setOnlyUnread(!onlyUnread)}
            className={clsx(
              'flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors',
              onlyUnread ? 'bg-brand-100 text-brand-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
            )}
          >
            <Filter size={12} /> Unread only
          </button>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <RefreshCw size={15} className={clsx(isFetching && 'animate-spin')} />
          </button>
          <button onClick={() => setShowCompose(true)} className="btn-primary py-1.5 text-xs px-3">
            Compose
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand-500" />
          </div>
        ) : error ? (
          <div className="card p-6 text-center">
            <AlertCircle size={24} className="text-red-400 mx-auto mb-2" />
            <p className="text-sm text-red-600">Failed to load emails</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="card p-8 text-center">
            <Mail size={32} className="text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500">{onlyUnread ? 'No unread emails' : 'Inbox is empty'}</p>
          </div>
        ) : (
          <div className="card divide-y divide-slate-50 overflow-auto">
            {messages.map((msg) => (
              <button
                key={msg.id}
                onClick={() => {
                  setSelectedMessage(msg)
                  setSummaryId(null)
                }}
                className={clsx(
                  'w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors',
                  selectedMessage?.id === msg.id && 'bg-brand-50',
                )}
              >
                <div className="flex items-start gap-2.5">
                  {!msg.is_read && (
                    <div className="w-2 h-2 bg-brand-500 rounded-full mt-2 flex-shrink-0" />
                  )}
                  {msg.is_read && <div className="w-2 flex-shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className={clsx('text-xs font-medium truncate', !msg.is_read ? 'text-slate-800' : 'text-slate-500')}>
                        {msg.sender_name}
                      </span>
                      <span className="text-xs text-slate-400 flex-shrink-0">
                        {formatRelativeTime(msg.received_at)}
                      </span>
                    </div>
                    <div className={clsx('text-sm truncate', !msg.is_read ? 'text-slate-800 font-medium' : 'text-slate-600')}>
                      {msg.importance === 'high' && (
                        <Star size={11} className="inline text-red-500 mr-1" />
                      )}
                      {msg.subject}
                    </div>
                    <p className="text-xs text-slate-400 truncate mt-0.5">{truncate(msg.preview, 60)}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Message detail / summary */}
      {selectedMessage && (
        <div className="flex flex-col gap-3">
          <div className="card p-5 flex-1">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className={clsx('text-base font-semibold text-slate-800', getImportanceColor(selectedMessage.importance))}>
                  {selectedMessage.subject}
                </h3>
                <p className="text-sm text-slate-500 mt-0.5">
                  From: <strong>{selectedMessage.sender_name}</strong> ({selectedMessage.sender_email})
                </p>
                <p className="text-xs text-slate-400">{formatRelativeTime(selectedMessage.received_at)}</p>
              </div>
              <div className="flex gap-2">
                {isSpeaking ? (
                  <button
                    onClick={handleStopReading}
                    className="btn-secondary py-1.5 text-xs flex items-center gap-1 text-red-600 border-red-200 hover:bg-red-50"
                  >
                    <VolumeX size={13} /> Stop
                  </button>
                ) : (
                  <button
                    onClick={() => handleReadAloud(selectedMessage)}
                    className="btn-secondary py-1.5 text-xs flex items-center gap-1"
                  >
                    <Volume2 size={13} /> Read Aloud
                  </button>
                )}
                <button
                  onClick={() => setSummaryId(summaryId ? null : selectedMessage.id)}
                  className="btn-secondary py-1.5 text-xs"
                >
                  {summaryId === selectedMessage.id ? 'Hide Summary' : 'Summarise'}
                </button>
              </div>
            </div>

            <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
              {selectedMessage.body_text ?? selectedMessage.preview}
            </div>
          </div>

          {/* Summary card */}
          {summaryId === selectedMessage.id && (
            <div>
              {summaryLoading ? (
                <div className="card p-6 flex items-center justify-center gap-2 text-slate-500 text-sm">
                  <Loader2 size={16} className="animate-spin" /> Generating summary...
                </div>
              ) : summary ? (
                <div className="flex flex-col gap-2">
                  <EmailSummaryCard summary={summary} />
                  <div className="flex justify-end">
                    {isSpeaking ? (
                      <button
                        onClick={handleStopReading}
                        className="btn-secondary py-1 text-xs flex items-center gap-1 text-red-600 border-red-200 hover:bg-red-50"
                      >
                        <VolumeX size={12} /> Stop
                      </button>
                    ) : (
                      <button
                        onClick={() => handleReadSummary(summary.summary_text)}
                        className="btn-secondary py-1 text-xs flex items-center gap-1"
                      >
                        <Volume2 size={12} /> Read Summary
                      </button>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      )}

      {/* Compose modal */}
      <ComposeModal isOpen={showCompose} onClose={() => setShowCompose(false)} />
    </div>
  )
}
