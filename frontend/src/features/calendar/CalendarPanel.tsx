import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, Users, Loader2, AlertCircle, RefreshCw, ChevronDown } from 'lucide-react'
import { clsx } from 'clsx'
import { calendarApi } from '@/services/api/calendar'
import { EventCard } from './EventCard'
import { ScheduleMeetingModal } from './ScheduleMeetingModal'
import { useAuthStore } from '@/hooks/useAuth'

type CalendarView = 'today' | 'week' | 'team'

// Demo team members available for managers to inspect
const TEAM_MEMBERS = [
  { name: 'Jamie Lee', email: 'jamie.lee@dev.local' },
  { name: 'Sarah Connor', email: 's.connor@contoso.com' },
  { name: 'John Smith', email: 'j.smith@contoso.com' },
  { name: 'Emma Thompson', email: 'e.thompson@contoso.com' },
  { name: 'David Walsh', email: 'd.walsh@contoso.com' },
]

export const CalendarPanel = () => {
  const [view, setView] = useState<CalendarView>('week')
  const [showSchedule, setShowSchedule] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState(TEAM_MEMBERS[0].email)
  const { hasPermission } = useAuthStore()
  const queryClient = useQueryClient()
  const canReadTeam = hasPermission('read_employee_calendar')

  // When the week cache is invalidated (e.g. after a voice meeting creation),
  // switch to week view so the new event is visible.
  useEffect(() => {
    const unsub = queryClient.getQueryCache().subscribe((event) => {
      if (
        event.type === 'updated' &&
        event.action.type === 'invalidate' &&
        Array.isArray(event.query.queryKey) &&
        event.query.queryKey[0] === 'calendar'
      ) {
        setView('week')
      }
    })
    return unsub
  }, [queryClient])

  const todayQuery = useQuery({
    queryKey: ['calendar', 'today'],
    queryFn: () => calendarApi.getToday(),
    enabled: view === 'today',
  })

  const weekQuery = useQuery({
    queryKey: ['calendar', 'week'],
    queryFn: () => calendarApi.getWeek(),
    enabled: view === 'week',
  })

  const teamQuery = useQuery({
    queryKey: ['calendar', 'employee', selectedEmployee],
    queryFn: () => calendarApi.getEmployeeCalendar(selectedEmployee),
    enabled: view === 'team' && canReadTeam,
  })

  const activeQuery = view === 'today' ? todayQuery : view === 'team' ? teamQuery : weekQuery
  const events = activeQuery.data?.events ?? []

  const selectedMember = TEAM_MEMBERS.find((m) => m.email === selectedEmployee)

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="card p-3 flex flex-wrap items-center gap-3">
        <div className="flex bg-slate-100 rounded-lg p-0.5">
          <button
            onClick={() => setView('today')}
            className={clsx('px-3 py-1.5 rounded-md text-sm font-medium transition-colors', view === 'today' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700')}
          >
            Today
          </button>
          <button
            onClick={() => setView('week')}
            className={clsx('px-3 py-1.5 rounded-md text-sm font-medium transition-colors', view === 'week' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700')}
          >
            This Week
          </button>
          {canReadTeam && (
            <button
              onClick={() => setView('team')}
              className={clsx('px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1', view === 'team' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700')}
            >
              <Users size={12} /> Team
            </button>
          )}
        </div>

        {/* Employee selector (only shown in team view) */}
        {view === 'team' && canReadTeam && (
          <div className="relative">
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="appearance-none text-xs bg-slate-50 border border-slate-200 rounded-lg pl-2.5 pr-6 py-1.5 text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-brand-400"
            >
              {TEAM_MEMBERS.map((m) => (
                <option key={m.email} value={m.email}>{m.name}</option>
              ))}
            </select>
            <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        )}

        <div className="flex-1" />
        <button
          onClick={() => activeQuery.refetch()}
          disabled={activeQuery.isFetching}
          className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
        >
          <RefreshCw size={15} className={clsx(activeQuery.isFetching && 'animate-spin')} />
        </button>
        <button onClick={() => setShowSchedule(true)} className="btn-primary py-1.5 text-xs px-3 flex items-center gap-1.5">
          <Plus size={14} /> Schedule
        </button>
      </div>

      {/* Team view header */}
      {view === 'team' && selectedMember && (
        <div className="flex items-center gap-2 px-1">
          <div className="w-6 h-6 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-xs font-bold flex-shrink-0">
            {selectedMember.name.charAt(0)}
          </div>
          <span className="text-sm font-medium text-slate-700">{selectedMember.name}'s calendar</span>
          <span className="text-xs text-slate-400">— this week</span>
        </div>
      )}

      {/* Events */}
      {activeQuery.isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-brand-500" />
        </div>
      ) : activeQuery.error ? (
        <div className="card p-6 text-center">
          <AlertCircle size={24} className="text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-600">Failed to load calendar</p>
        </div>
      ) : events.length === 0 ? (
        <div className="card p-10 text-center">
          <Calendar size={36} className="text-slate-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-500">
            {view === 'today' ? 'No meetings today' : view === 'team' ? `${selectedMember?.name ?? 'They'} has no meetings this week` : 'No meetings this week'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            {view === 'team' ? 'Their schedule is clear.' : 'Your schedule is clear.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <EventCard key={event.event_id} event={event} />
          ))}
        </div>
      )}

      <ScheduleMeetingModal isOpen={showSchedule} onClose={() => setShowSchedule(false)} />
    </div>
  )
}
