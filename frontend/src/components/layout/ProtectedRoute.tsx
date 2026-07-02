import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/hooks/useAuth'
import type { UserRole } from '@/types'

interface ProtectedRouteProps {
  requiredRole?: UserRole
}

const ROLE_LEVEL: Record<UserRole, number> = {
  employee: 1,
  manager: 2,
  admin: 3,
}

export const ProtectedRoute = ({ requiredRole }: ProtectedRouteProps) => {
  const { token, user } = useAuthStore()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (requiredRole && user) {
    const userLevel = ROLE_LEVEL[user.role] ?? 0
    const requiredLevel = ROLE_LEVEL[requiredRole] ?? 0
    if (userLevel < requiredLevel) {
      return (
        <div className="flex items-center justify-center h-full p-8">
          <div className="card p-8 text-center max-w-md">
            <h2 className="text-xl font-semibold text-slate-800 mb-2">Access Denied</h2>
            <p className="text-slate-500">
              You need the <strong>{requiredRole}</strong> role to access this section.
              Contact your administrator to request access.
            </p>
          </div>
        </div>
      )
    }
  }

  return <Outlet />
}
