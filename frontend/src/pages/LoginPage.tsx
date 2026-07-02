import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cpu, Shield, LogIn, Loader2 } from 'lucide-react'
import { authApi } from '@/services/api/auth'
import { useAuthStore } from '@/hooks/useAuth'
import toast from 'react-hot-toast'


const DEMO_ROLES = [
  { role: 'manager', name: 'Alex Morgan', label: 'Manager', description: 'Full email, calendar, voice, scheduling' },
  { role: 'admin', name: 'Admin User', label: 'Admin', description: 'All permissions + audit logs + diagnostics' },
  { role: 'employee', name: 'Jamie Lee', label: 'Employee', description: 'Own email and calendar, read-only' },
]

export const LoginPage = () => {
  const navigate = useNavigate()
  const { setToken, setUser } = useAuthStore()
  const [loading, setLoading] = useState<string | null>(null)

  const handleMockLogin = async (role: string, name: string) => {
    setLoading(role)
    try {
      const { access_token } = await authApi.mockLogin(role, name)
      setToken(access_token)
      const user = await authApi.getMe()
      setUser(user)
      navigate('/dashboard')
    } catch (err) {
      toast.error('Failed to sign in. Please try again.')
    } finally {
      setLoading(null)
    }
  }

  const handleMicrosoftLogin = async () => {
    setLoading('microsoft')
    try {
      const { auth_url } = await authApi.getLoginUrl()
      window.location.href = auth_url
    } catch {
      toast.error('Failed to initiate Microsoft login.')
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-800 to-brand-700 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-2xl mb-4">
            <Cpu size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Convo</h1>
          <p className="text-brand-200 text-sm mt-1">Intelligent Personal Assistant</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Microsoft Login */}
          <div className="p-6 border-b border-slate-100">
            <button
              onClick={handleMicrosoftLogin}
              disabled={loading !== null}
              className="w-full flex items-center justify-center gap-3 bg-[#0078d4] hover:bg-[#106ebe] text-white font-medium py-3 px-4 rounded-xl transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading === 'microsoft' ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <MicrosoftIcon />
              )}
              Sign in with Microsoft
            </button>
            <p className="text-xs text-slate-400 text-center mt-3 flex items-center justify-center gap-1">
              <Shield size={11} /> Secured via Microsoft OAuth 2.0
            </p>
          </div>

          {/* Demo Mode */}
          <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex-1 h-px bg-slate-200" />
              <span className="text-xs text-slate-400 px-2">Demo Mode</span>
              <div className="flex-1 h-px bg-slate-200" />
            </div>
            <p className="text-xs text-slate-500 text-center mb-4">
              Sign in with a demo account to explore features without Azure credentials.
            </p>
            <div className="space-y-2">
              {DEMO_ROLES.map(({ role, name, label, description }) => (
                <button
                  key={role}
                  onClick={() => handleMockLogin(role, name)}
                  disabled={loading !== null}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:border-brand-300 hover:bg-brand-50 transition-colors text-left disabled:opacity-60 disabled:cursor-not-allowed group"
                >
                  {loading === role ? (
                    <Loader2 size={16} className="animate-spin text-brand-500 flex-shrink-0" />
                  ) : (
                    <LogIn size={16} className="text-slate-400 group-hover:text-brand-500 flex-shrink-0" />
                  )}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-700">{name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                        role === 'admin' ? 'bg-purple-100 text-purple-700' :
                        role === 'manager' ? 'bg-blue-100 text-blue-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>{label}</span>
                    </div>
                    <p className="text-xs text-slate-400 truncate">{description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-brand-300 mt-6">
          Contoso Corporation &copy; {new Date().getFullYear()} — Academic Prototype
        </p>
      </div>
    </div>
  )
}

const MicrosoftIcon = () => (
  <svg width="18" height="18" viewBox="0 0 21 21" fill="none">
    <rect x="1" y="1" width="9" height="9" fill="#f25022" />
    <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
    <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
    <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
  </svg>
)
