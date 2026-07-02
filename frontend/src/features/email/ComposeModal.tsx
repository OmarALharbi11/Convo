import { useState } from 'react'
import { X, Send, AlertTriangle } from 'lucide-react'
import { emailApi } from '@/services/api/email'
import toast from 'react-hot-toast'

interface ComposeModalProps {
  isOpen: boolean
  onClose: () => void
  initialTo?: string
  initialSubject?: string
}

export const ComposeModal = ({ isOpen, onClose, initialTo = '', initialSubject = '' }: ComposeModalProps) => {
  const [to, setTo] = useState(initialTo)
  const [subject, setSubject] = useState(initialSubject)
  const [body, setBody] = useState('')
  const [cc, setCc] = useState('')
  const [showCc, setShowCc] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [sending, setSending] = useState(false)

  if (!isOpen) return null

  const toList = to.split(',').map((e) => e.trim()).filter(Boolean)
  const ccList = cc.split(',').map((e) => e.trim()).filter(Boolean)
  const isValid = toList.length > 0 && subject.trim() && body.trim()

  const handleSendClick = () => {
    if (!isValid) {
      toast.error('Please fill in all required fields.')
      return
    }
    setConfirming(true)
  }

  const handleConfirmSend = async () => {
    setSending(true)
    try {
      await emailApi.sendEmail({ to: toList, subject, body, cc: ccList })
      toast.success('Email sent successfully.')
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to send email.')
    } finally {
      setSending(false)
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h3 className="text-base font-semibold text-slate-800">Compose Email</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={18} />
          </button>
        </div>

        {!confirming ? (
          <div className="p-5 space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">To *</label>
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="email@company.com, another@company.com"
                className="input text-sm"
              />
            </div>

            {showCc ? (
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">CC</label>
                <input value={cc} onChange={(e) => setCc(e.target.value)} placeholder="cc@company.com" className="input text-sm" />
              </div>
            ) : (
              <button onClick={() => setShowCc(true)} className="text-xs text-brand-500 hover:text-brand-700">
                + Add CC
              </button>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Subject *</label>
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Email subject"
                className="input text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Message *</label>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write your message..."
                rows={6}
                className="input text-sm resize-none"
              />
              <p className="text-xs text-slate-400 mt-1 text-right">{body.length} characters</p>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button onClick={onClose} className="btn-secondary">Cancel</button>
              <button onClick={handleSendClick} disabled={!isValid} className="btn-primary flex items-center gap-2">
                <Send size={14} /> Review & Send
              </button>
            </div>
          </div>
        ) : (
          <div className="p-5">
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-amber-800">Review before sending</p>
                  <div className="text-sm text-amber-700 mt-2 space-y-1">
                    <p><strong>To:</strong> {toList.join(', ')}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <p><strong>Body:</strong> {body.slice(0, 80)}{body.length > 80 ? '...' : ''}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirming(false)} className="btn-secondary">Back to Edit</button>
              <button onClick={handleConfirmSend} disabled={sending} className="btn-primary flex items-center gap-2">
                {sending ? 'Sending...' : <><Send size={14} /> Send Now</>}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
