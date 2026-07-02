import { AuditLogViewer } from '@/features/audit/AuditLogViewer'

export const AuditPage = () => (
  <div className="max-w-5xl mx-auto">
    <h1 className="text-xl font-bold text-slate-800 mb-6">Audit Log</h1>
    <AuditLogViewer />
  </div>
)
