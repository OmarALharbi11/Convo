import { useState } from 'react'
import { MapPin, Users, Video, Pencil, Trash2, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { formatTime, formatDate, formatDuration } from '@/utils/formatting'
import { calendarApi } from '@/services/api/calendar'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import type { CalendarEvent } from '@/types'
import { EditMeetingModal } from './EditMeetingModal'

interface EventCardProps {
  event: CalendarEvent
  compact?: boolean
}

export const EventCard = ({ event, compact = false }: EventCardProps) => {
  const qc = useQueryClient()
  const [showEdit, setShowEdit] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const duration = formatDuration(event.start, event.end)
  const isNow = (() => {
    const now = Date.now()
    return new Date(event.start).getTime() <= now && new Date(event.end).getTime() >= now
  })()

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${event.subject}"?`)) return
    setDeleting(true)
    try {
      await calendarApi.deleteEvent(event.event_id)
      toast.success('Meeting deleted.')
      qc.invalidateQueries({ queryKey: ['calendar'] })
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete meeting.')
      setDeleting(false)
    }
  }

  return (
    <>
      <div className={clsx(
        'card p-4 hover:shadow-md transition-shadow group',
        isNow && 'ring-2 ring-brand-500 border-brand-200',
      )}>
        <div className="flex items-start gap-3">
          {/* Time column */}
          <div className="flex-shrink-0 text-right w-20">
            <div className="text-xs font-medium text-slate-500">{formatDate(event.start)}</div>
            <div className="text-sm font-semibold text-slate-700">{formatTime(event.start)}</div>
            <div className="text-xs text-slate-400">{duration}</div>
          </div>

          {/* Left accent bar */}
          <div className={clsx('w-1 rounded-full self-stretch flex-shrink-0', isNow ? 'bg-brand-500' : 'bg-slate-200')} />

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="text-sm font-semibold text-slate-800 leading-snug">{event.subject}</h4>
                {isNow && (
                  <span className="inline-block text-xs bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full font-medium mt-1">
                    Now
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                {event.is_online_meeting && event.meeting_url && (
                  <a
                    href={event.meeting_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-800 bg-brand-50 px-2 py-1 rounded-lg"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Video size={12} /> Join
                  </a>
                )}
                <button
                  onClick={() => setShowEdit(true)}
                  className="p-1.5 text-slate-300 hover:text-brand-500 hover:bg-brand-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                  title="Edit meeting"
                >
                  <Pencil size={13} />
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                  title="Delete meeting"
                >
                  {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                </button>
              </div>
            </div>

            {!compact && (
              <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
                {event.location && (
                  <span className="flex items-center gap-1">
                    <MapPin size={11} /> {event.location}
                  </span>
                )}
                {event.attendees.length > 0 && (
                  <span className="flex items-center gap-1">
                    <Users size={11} /> {event.attendees.length} attendee{event.attendees.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {showEdit && <EditMeetingModal event={event} onClose={() => setShowEdit(false)} />}
    </>
  )
}
