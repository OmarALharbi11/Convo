import { X, LogOut, Mail, Shield, User } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  manager: 'bg-blue-100 text-blue-700',
  employee: 'bg-slate-100 text-slate-600',
}

const PERMISSION_LABELS: Record<string, string> = {
  read_own_email: 'Read own email',
  send_email: 'Send email',
  read_own_calendar: 'Read own calendar',
  write_own_calendar: 'Write own calendar',
  read_employee_calendar: 'Read team calendars',
  schedule_meeting: 'Schedule meetings',
  modify_any_meeting: 'Modify any meeting',
  manage_users: 'Manage users',
  view_audit_log: 'View audit log',
  access_diagnostics: 'View diagnostics',
}

interface UserProfileModalProps {
  isOpen: boolean
  onClose: () => void
}

export const UserProfileModal = ({ isOpen, onClose }: UserProfileModalProps) => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  if (!isOpen || !user) return null

  const initials = user.display_name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  const handleLogout = () => {
    logout()
    onClose()
    navigate('/login')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end p-4 pt-16">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-80 overflow-hidden">
        {/* Header */}
        <div className="bg-brand-600 px-5 py-6">
          <button
            onClick={onClose}
            className="absolute top-3 right-3 text-white/60 hover:text-white transition-colors"
          >
            <X size={16} />
          </button>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
              {initials}
            </div>
            <div className="min-w-0">
              <div className="text-white font-semibold text-base truncate">{user.display_name}</div>
              <div className="text-brand-200 text-xs truncate mt-0.5">{user.email}</div>
              <span className={clsx('inline-block mt-1.5 px-2 py-0.5 rounded-full text-xs font-medium capitalize', ROLE_COLORS[user.role] ?? 'bg-gray-100 text-gray-600')}>
                {user.role}
              </span>
            </div>
          </div>
        </div>

        {/* Permissions */}
        <div className="px-5 py-4">
          <div className="flex items-center gap-1.5 mb-3">
            <Shield size={13} className="text-slate-400" />
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Permissions</span>
          </div>
          <div className="grid grid-cols-1 gap-1">
            {user.permissions.map((perm) => (
              <div key={perm} className="flex items-center gap-2 text-xs text-slate-600">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                {PERMISSION_LABELS[perm] ?? perm.replace(/_/g, ' ')}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 pb-4 pt-2 border-t border-slate-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut size={15} />
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
