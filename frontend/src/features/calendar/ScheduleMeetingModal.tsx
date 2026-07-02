import { useState } from 'react'
import { X, Plus, Trash2, Calendar, Loader2 } from 'lucide-react'
import { calendarApi } from '@/services/api/calendar'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { format, addHours } from 'date-fns'

interface ScheduleMeetingModalProps {
  isOpen: boolean
  onClose: () => void
}

export const ScheduleMeetingModal = ({ isOpen, onClose }: ScheduleMeetingModalProps) => {
  const qc = useQueryClient()
  const now = new Date()
  const defaultStart = format(addHours(now, 1), "yyyy-MM-dd'T'HH:00")
  const defaultEnd = format(addHours(now, 2), "yyyy-MM-dd'T'HH:00")

  const [subject, setSubject] = useState('')
  const [start, setStart] = useState(defaultStart)
  const [end, setEnd] = useState(defaultEnd)
  const [location, setLocation] = useState('')
  const [attendeeInput, setAttendeeInput] = useState('')
  const [attendees, setAttendees] = useState<string[]>([])
  const [isOnline, setIsOnline] = useState(false)
  const [saving, setSaving] = useState(false)

  if (!isOpen) return null

  const addAttendee = () => {
    const email = attendeeInput.trim()
    if (email && !attendees.includes(email)) {
      setAttendees([...attendees, email])
      setAttendeeInput('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!subject.trim()) { toast.error('Please enter a meeting title.'); return }
    if (new Date(end) <= new Date(start)) { toast.error('End time must be after start time.'); return }

    setSaving(true)
    try {
      await calendarApi.createEvent({
        subject,
        start: new Date(start).toISOString(),
        end: new Date(end).toISOString(),
        attendees,
        location: location || undefined,
        is_online_meeting: isOnline,
      })
      toast.success('Meeting scheduled successfully.')
      qc.invalidateQueries({ queryKey: ['calendar'] })
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create meeting.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 sticky top-0 bg-white">
          <h3 className="text-base font-semibold text-slate-800 flex items-center gap-2">
            <Calendar size={18} className="text-brand-500" /> Schedule Meeting
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Title *</label>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Meeting title" className="input text-sm" required />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Start *</label>
              <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} className="input text-sm" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">End *</label>
              <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} className="input text-sm" required />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Location</label>
            <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Room, address, or leave blank" className="input text-sm" />
          </div>

          <div className="flex items-center gap-2">
            <input type="checkbox" id="online" checked={isOnline} onChange={(e) => setIsOnline(e.target.checked)} className="rounded" />
            <label htmlFor="online" className="text-sm text-slate-700">Online meeting (Teams link)</label>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Attendees</label>
            <div className="flex gap-2 mb-2">
              <input
                value={attendeeInput}
                onChange={(e) => setAttendeeInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addAttendee() } }}
                placeholder="colleague@company.com"
                className="input text-sm flex-1"
              />
              <button type="button" onClick={addAttendee} className="btn-secondary py-2 px-3"><Plus size={15} /></button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {attendees.map((email) => (
                <span key={email} className="flex items-center gap-1 bg-brand-50 text-brand-700 px-2 py-1 rounded-lg text-xs">
                  {email}
                  <button type="button" onClick={() => setAttendees(attendees.filter((a) => a !== email))}>
                    <Trash2 size={11} />
                  </button>
                </span>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Calendar size={14} />}
              {saving ? 'Scheduling...' : 'Schedule Meeting'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
