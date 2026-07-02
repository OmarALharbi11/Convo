import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Mail,
  Calendar,
  ClipboardList,
  Settings,
  LogOut,
  Bell,
  Wifi,
  WifiOff,
  UserCircle,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '@/hooks/useAuth'
import { useState, useEffect } from 'react'
import { UserProfileModal } from '@/components/ui/UserProfileModal'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, minRole: 'employee' },
  { path: '/email', label: 'Email', icon: Mail, minRole: 'employee' },
  { path: '/calendar', label: 'Calendar', icon: Calendar, minRole: 'employee' },
  { path: '/audit', label: 'Audit Log', icon: ClipboardList, minRole: 'manager' },
  { path: '/admin', label: 'Admin', icon: Settings, minRole: 'admin' },
  { path: '/account', label: 'Account', icon: UserCircle, minRole: 'employee' },
]

const ROLE_LEVEL: Record<string, number> = { employee: 1, manager: 2, admin: 3 }

const RoleBadge = ({ role }: { role: string }) => {
  const colors: Record<string, string> = {
    admin: 'bg-red-100 text-red-700',
    manager: 'bg-brand-100 text-brand-700',
    employee: 'bg-slate-100 text-slate-600',
  }
  return (
    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium capitalize', colors[role] ?? 'bg-gray-100')}>
      {role}
    </span>
  )
}

export const AppShell = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [mockMode, setMockMode] = useState(true)
  const [showProfile, setShowProfile] = useState(false)

  useEffect(() => {
    fetch('/api/auth/status')
      .then((r) => r.json())
      .then((d) => setMockMode(d.mock_mode ?? true))
      .catch(() => {})
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userRoleLevel = ROLE_LEVEL[user?.role ?? 'employee'] ?? 1

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-brand-900 flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-brand-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">C</span>
            </div>
            <div>
              <div className="text-white font-semibold text-sm">Convo</div>
              <div className="text-brand-300 text-xs">v1.0.0</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.filter((item) => ROLE_LEVEL[item.minRole] <= userRoleLevel).map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-brand-200 hover:bg-brand-800 hover:text-white',
                )}
              >
                <item.icon size={18} />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* User info */}
        {user && (
          <div className="px-4 py-4 border-t border-brand-800">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                {user.display_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white text-xs font-medium truncate">{user.display_name}</div>
                <div className="text-brand-300 text-xs truncate">{user.email}</div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <RoleBadge role={user.role} />
              <button
                onClick={handleLogout}
                className="text-brand-300 hover:text-white transition-colors p-1 rounded"
                title="Sign out"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top header */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center px-6 gap-4 flex-shrink-0">
          <div className="flex-1" />
          {/* Mock mode indicator */}
          <div className={clsx(
            'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium',
            mockMode ? 'bg-amber-50 text-amber-700' : 'bg-green-50 text-green-700',
          )}>
            {mockMode ? <WifiOff size={12} /> : <Wifi size={12} />}
            {mockMode ? 'Demo Mode' : 'Live Mode'}
          </div>
          {/* Notifications */}
          <button className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors rounded-lg hover:bg-slate-100">
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
          </button>

          {/* User avatar */}
          {user && (
            <button
              onClick={() => setShowProfile(true)}
              className="w-8 h-8 rounded-full bg-brand-600 hover:bg-brand-700 flex items-center justify-center text-white text-xs font-bold transition-colors ring-2 ring-transparent hover:ring-brand-300"
              title={user.display_name}
            >
              {user.display_name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()}
            </button>
          )}
        </header>

        <UserProfileModal isOpen={showProfile} onClose={() => setShowProfile(false)} />

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
