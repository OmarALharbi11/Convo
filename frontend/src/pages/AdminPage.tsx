import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/services/api/admin'
import { Loader2, AlertCircle, CheckCircle, XCircle, Activity } from 'lucide-react'
import { clsx } from 'clsx'

export const AdminPage = () => {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['admin', 'diagnostics'],
    queryFn: adminApi.getDiagnostics,
    refetchInterval: 30_000,
  })

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-slate-800">Admin Diagnostics</h1>
        <button onClick={() => refetch()} className="btn-secondary py-1.5 text-xs px-3 flex items-center gap-1.5">
          <Activity size={13} /> Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 size={24} className="animate-spin text-brand-500" />
        </div>
      ) : error ? (
        <div className="card p-6 text-center">
          <AlertCircle size={24} className="text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-600">Failed to load diagnostics</p>
        </div>
      ) : data ? (
        <div className="space-y-4">
          {/* System Status */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">System Status</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <StatusItem label="Environment" value={data.environment} />
              <StatusItem label="Version" value={data.version} />
              <StatusItem label="Uptime" value={data.uptime} />
            </div>
          </div>

          {/* Feature Flags */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">Feature Flags</h2>
            <div className="grid grid-cols-2 gap-3">
              <FlagItem label="Mock Graph API" enabled={data.mock_mode?.graph} />
              <FlagItem label="Mock STT" enabled={data.mock_mode?.stt} />
              <FlagItem label="Mock TTS" enabled={data.mock_mode?.tts} />
              <FlagItem label="LLM Intent Parser" enabled={data.llm_intent_enabled} />
            </div>
          </div>

          {/* Intent Classifier Debug */}
          {data.last_intent_debug && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Last Voice Command</h2>
              <div className="bg-slate-50 rounded-lg p-3 font-mono text-xs text-slate-700 overflow-auto max-h-64">
                <pre>{JSON.stringify(data.last_intent_debug, null, 2)}</pre>
              </div>
            </div>
          )}

          {/* Audit Stats */}
          {data.audit_stats && (
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-4">Audit Statistics (last 24h)</h2>
              <div className="grid grid-cols-3 gap-3">
                <StatCard label="Total Events" value={data.audit_stats.total} />
                <StatCard label="Successful" value={data.audit_stats.success} color="text-green-600" />
                <StatCard label="Denied" value={data.audit_stats.denied} color="text-red-600" />
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}

const StatusItem = ({ label, value }: { label: string; value?: string | number }) => (
  <div className="bg-slate-50 rounded-lg p-3">
    <div className="text-xs text-slate-500 mb-1">{label}</div>
    <div className="text-sm font-medium text-slate-800">{value ?? '—'}</div>
  </div>
)

const FlagItem = ({ label, enabled }: { label: string; enabled?: boolean }) => (
  <div className="flex items-center gap-2">
    {enabled ? (
      <CheckCircle size={16} className="text-green-500 flex-shrink-0" />
    ) : (
      <XCircle size={16} className="text-slate-300 flex-shrink-0" />
    )}
    <span className={clsx('text-sm', enabled ? 'text-slate-700' : 'text-slate-400')}>{label}</span>
  </div>
)

const StatCard = ({ label, value, color = 'text-slate-800' }: { label: string; value?: number; color?: string }) => (
  <div className="bg-slate-50 rounded-lg p-3 text-center">
    <div className={clsx('text-2xl font-bold', color)}>{value ?? 0}</div>
    <div className="text-xs text-slate-500 mt-1">{label}</div>
  </div>
)
