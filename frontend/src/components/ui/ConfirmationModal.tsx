import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Send, Trash2, Edit, X, CalendarPlus } from 'lucide-react'
import { clsx } from 'clsx'

type ActionType = 'send-email' | 'create-meeting' | 'modify-calendar' | 'delete-event' | 'generic'

interface ConfirmationModalProps {
  isOpen: boolean
  title: string
  message: string
  actionType?: ActionType
  onConfirm: () => void
  onCancel: () => void
  autoCloseSeconds?: number
}

const ACTION_CONFIG: Record<ActionType, { icon: React.ReactNode; color: string; confirmLabel: string }> = {
  'send-email': {
    icon: <Send size={20} />,
    color: 'bg-blue-600 hover:bg-blue-700',
    confirmLabel: 'Send Email',
  },
  'create-meeting': {
    icon: <CalendarPlus size={20} />,
    color: 'bg-brand-600 hover:bg-brand-700',
    confirmLabel: 'Schedule Meeting',
  },
  'modify-calendar': {
    icon: <Edit size={20} />,
    color: 'bg-yellow-600 hover:bg-yellow-700',
    confirmLabel: 'Reschedule',
  },
  'delete-event': {
    icon: <Trash2 size={20} />,
    color: 'bg-red-600 hover:bg-red-700',
    confirmLabel: 'Cancel Meeting',
  },
  generic: {
    icon: <AlertTriangle size={20} />,
    color: 'bg-brand-600 hover:bg-brand-700',
    confirmLabel: 'Confirm',
  },
}

export const ConfirmationModal = ({
  isOpen,
  title,
  message,
  actionType = 'generic',
  onConfirm,
  onCancel,
  autoCloseSeconds,
}: ConfirmationModalProps) => {
  const config = ACTION_CONFIG[actionType]
  const [secondsLeft, setSecondsLeft] = useState(autoCloseSeconds ?? 0)
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!isOpen) return
    cancelRef.current?.focus()
    if (!autoCloseSeconds) return

    setSecondsLeft(autoCloseSeconds)
    const interval = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) { clearInterval(interval); onCancel(); return 0 }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [isOpen, autoCloseSeconds])

  // Close on ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape' && isOpen) onCancel() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onCancel])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X size={18} />
        </button>

        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          <div className={clsx('p-2.5 rounded-xl text-white', config.color)}>
            {config.icon}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
            <p className="text-sm text-slate-500 mt-1">This action requires your confirmation.</p>
          </div>
        </div>

        {/* Message */}
        <div className="bg-slate-50 rounded-xl p-4 mb-6">
          <p className="text-sm text-slate-700 leading-relaxed">{message}</p>
        </div>

        {/* Auto-close countdown */}
        {autoCloseSeconds && secondsLeft > 0 && (
          <p className="text-xs text-slate-400 mb-4 text-center">
            Auto-cancelling in {secondsLeft}s
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            ref={cancelRef}
            onClick={onCancel}
            className="flex-1 btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={clsx('flex-1 text-white px-4 py-2 rounded-lg font-medium transition-all active:scale-95', config.color)}
          >
            {config.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
