import { LogOut, Shield, User, Mail, Settings, Bell, Globe, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

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

export const AccountPage = () => {
  const { user, logout, isLoading } = useAuth()
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState(true)
  const [language, setLanguage] = useState('English')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={24} className="animate-spin text-brand-500" />
      </div>
    )
  }

  if (!user) return null

  const initials = user.display_name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="max-w-xl mx-auto flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-slate-800">Account & Settings</h1>

      {/* Profile card */}
      <div className="card overflow-hidden">
        <div className="bg-brand-600 px-6 py-6 flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="text-white font-semibold text-lg truncate">{user.display_name}</div>
            <div className="text-brand-200 text-sm truncate mt-0.5">{user.email}</div>
            <span className={clsx('inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', ROLE_COLORS[user.role] ?? 'bg-gray-100 text-gray-600')}>
              {user.role}
            </span>
          </div>
        </div>
        <div className="px-6 py-4 flex flex-col gap-3">
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <User size={15} className="text-slate-400" />
            <span>{user.display_name}</span>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <Mail size={15} className="text-slate-400" />
            <span>{user.email}</span>
          </div>
        </div>
      </div>

      {/* Permissions */}
      <div className="card px-6 py-4">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={15} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Permissions</span>
        </div>
        <div className="grid grid-cols-1 gap-2">
          {(user.permissions ?? []).map((perm) => (
            <div key={perm} className="flex items-center gap-2.5 text-sm text-slate-600">
              <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
              {PERMISSION_LABELS[perm] ?? perm.replace(/_/g, ' ')}
            </div>
          ))}
        </div>
      </div>

      {/* Settings */}
      <div className="card px-6 py-4">
        <div className="flex items-center gap-2 mb-4">
          <Settings size={15} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Settings</span>
        </div>
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell size={15} className="text-slate-400" />
              <div>
                <div className="text-sm font-medium text-slate-700">Notifications</div>
                <div className="text-xs text-slate-400">Receive system alerts</div>
              </div>
            </div>
            <button
              onClick={() => setNotifications(!notifications)}
              className={clsx('relative w-10 h-5 rounded-full transition-colors', notifications ? 'bg-brand-600' : 'bg-slate-200')}
            >
              <span className={clsx('absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform', notifications ? 'translate-x-5' : 'translate-x-0.5')} />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Globe size={15} className="text-slate-400" />
              <div>
                <div className="text-sm font-medium text-slate-700">Language</div>
                <div className="text-xs text-slate-400">Interface language</div>
              </div>
            </div>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1 text-slate-600 bg-white"
            >
              <option>English</option>
              <option>French</option>
              <option>Spanish</option>
              <option>Arabic</option>
            </select>
          </div>
        </div>
      </div>

      {/* Sign out */}
      <div className="card px-6 py-4">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 border border-red-200 transition-colors"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </div>
  )
}
