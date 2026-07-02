import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Shield, Loader2, AlertCircle, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { auditApi } from '@/services/api/audit'
import { getAuditOutcomeColor } from '@/utils/formatting'
import { formatDateTime } from '@/utils/formatting'
import type { AuditEntry } from '@/types'

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'auth.login', label: 'Login' },
  { value: 'auth.logout', label: 'Logout' },
  { value: 'email.read', label: 'Email Read' },
  { value: 'email.send', label: 'Email Send' },
  { value: 'calendar.read', label: 'Calendar Read' },
  { value: 'calendar.create_event', label: 'Event Created' },
  { value: 'calendar.update_event', label: 'Event Updated' },
  { value: 'calendar.delete_event', label: 'Event Deleted' },
  { value: 'voice.command', label: 'Voice Command' },
  { value: 'permission.denied', label: 'Permission Denied' },
]

const OUTCOME_OPTIONS = [
  { value: '', label: 'All Outcomes' },
  { value: 'success', label: 'Success' },
  { value: 'failure', label: 'Failure' },
  { value: 'denied', label: 'Denied' },
]

const PAGE_SIZE = 20

export const AuditLogViewer = () => {
  const [actionFilter, setActionFilter] = useState('')
  const [outcomeFilter, setOutcomeFilter] = useState('')
  const [page, setPage] = useState(0)

  const { data, isLoading, error } = useQuery({
    queryKey: ['audit', 'all', actionFilter, page],
    queryFn: () =>
      auditApi.getLogs({
        action_filter: actionFilter || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
  })

  const entries = data?.entries ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="card p-3 flex flex-wrap items-center gap-3">
        <Filter size={15} className="text-slate-400" />
        <select
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(0) }}
          className="input text-sm py-1.5 w-44"
        >
          {ACTION_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          value={outcomeFilter}
          onChange={(e) => { setOutcomeFilter(e.target.value); setPage(0) }}
          className="input text-sm py-1.5 w-40"
        >
          {OUTCOME_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <span className="text-xs text-slate-400 ml-auto">{total} total entries</span>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-brand-500" />
        </div>
      ) : error ? (
        <div className="card p-6 text-center">
          <AlertCircle size={24} className="text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-600">Failed to load audit logs</p>
        </div>
      ) : entries.length === 0 ? (
        <div className="card p-10 text-center">
          <Shield size={36} className="text-slate-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-500">No audit entries found</p>
          <p className="text-xs text-slate-400 mt-1">Adjust your filters to see results.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500">Timestamp</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500">User</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500">Role</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500">Action</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500">Resource</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {entries.map((entry: AuditEntry) => (
                  <AuditRow key={entry.id} entry={entry} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-slate-600">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}

const AuditRow = ({ entry }: { entry: AuditEntry }) => (
  <tr className="hover:bg-slate-50 transition-colors">
    <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">
      {formatDateTime(entry.timestamp)}
    </td>
    <td className="px-4 py-2.5">
      <div className="text-xs font-medium text-slate-700">{entry.actor_email}</div>
      {entry.ip_address && (
        <div className="text-xs text-slate-400">{entry.ip_address}</div>
      )}
    </td>
    <td className="px-4 py-2.5">
      <span className={clsx(
        'px-1.5 py-0.5 rounded text-xs font-medium',
        entry.actor_role === 'admin' && 'bg-purple-100 text-purple-700',
        entry.actor_role === 'manager' && 'bg-blue-100 text-blue-700',
        entry.actor_role === 'employee' && 'bg-slate-100 text-slate-600',
      )}>
        {entry.actor_role}
      </span>
    </td>
    <td className="px-4 py-2.5">
      <span className="text-xs font-mono text-slate-600">{entry.action}</span>
    </td>
    <td className="px-4 py-2.5 text-xs text-slate-500 max-w-[200px] truncate">
      {entry.target_resource || '—'}
    </td>
    <td className="px-4 py-2.5">
      <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium', getAuditOutcomeColor(entry.outcome))}>
        {entry.outcome}
      </span>
    </td>
  </tr>
)
