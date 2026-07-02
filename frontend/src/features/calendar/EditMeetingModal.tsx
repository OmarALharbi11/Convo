import { useState } from 'react'
import { X, Plus, Trash2, Pencil, Loader2 } from 'lucide-react'
import { calendarApi } from '@/services/api/calendar'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import type { CalendarEvent } from '@/types'

interface EditMeetingModalProps {
  event: CalendarEvent
  onClose: () => void
}

function toLocalDatetimeValue(iso: string): string {
  const d = new Date(iso)
  return format(d, "yyyy-MM-dd'T'HH:mm")
}

export const EditMeetingModal = ({ event, onClose }: EditMeetingModalProps) => {
  const qc = useQueryClient()

  const [subject, setSubject] = useState(event.subject)
  const [start, setStart] = useState(toLocalDatetimeValue(event.start))
  const [end, setEnd] = useState(toLocalDatetimeValue(event.end))
  const [location, setLocation] = useState(event.location ?? '')
  const [attendeeInput, setAttendeeInput] = useState('')
  const [attendees, setAttendees] = useState<string[]>(event.attendees ?? [])
  const [saving, setSaving] = useState(false)

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
      await calendarApi.updateEvent(event.event_id, {
        subject,
        start: new Date(start).toISOString(),
        end: new Date(end).toISOString(),
        attendees,
        location: location || undefined,
      })
      toast.success('Meeting updated.')
      qc.invalidateQueries({ queryKey: ['calendar'] })
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update meeting.')
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
            <Pencil size={18} className="text-brand-500" /> Edit Meeting
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Title *</label>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} className="input text-sm" required />
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
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Pencil size={14} />}
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
