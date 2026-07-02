import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { authApi } from '@/services/api/auth'
import { useAuthStore } from '@/hooks/useAuth'
import toast from 'react-hot-toast'

export const OAuthCallbackPage = () => {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const setToken = useAuthStore((s) => s.setToken)

  useEffect(() => {
    const code = params.get('code')
    const state = params.get('state')
    const error = params.get('error')

    if (error) {
      toast.error('Microsoft login was cancelled or failed.')
      navigate('/login')
      return
    }

    if (!code) {
      navigate('/login')
      return
    }

    authApi.callback(code, state ?? undefined)
      .then(({ access_token }) => {
        setToken(access_token)
        navigate('/dashboard')
      })
      .catch(() => {
        toast.error('Authentication failed. Please try again.')
        navigate('/login')
      })
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-50">
      <div className="text-center">
        <Loader2 size={32} className="animate-spin text-brand-500 mx-auto mb-3" />
        <p className="text-sm text-slate-600">Completing sign-in…</p>
      </div>
    </div>
  )
}
