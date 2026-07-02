import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useEffect } from 'react'
import { authApi } from '@/services/api/auth'
import type { User, UserRole } from '@/types'

interface AuthState {
  token: string | null
  user: User | null
  isLoading: boolean
  isInitialized: boolean
  setToken: (token: string) => void
  setUser: (user: User) => void
  logout: () => void
  hasPermission: (permission: string) => boolean
  isAtLeast: (role: UserRole) => boolean
}

const ROLE_LEVEL: Record<UserRole, number> = {
  employee: 1,
  manager: 2,
  admin: 3,
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: false,
      isInitialized: false,

      setToken: (token) => set({ token }),
      setUser: (user) => set({ user, isInitialized: true }),

      logout: () => {
        authApi.logout().catch(() => {})
        set({ token: null, user: null, isInitialized: true })
      },

      hasPermission: (permission) => {
        const user = get().user
        return user?.permissions?.includes(permission) ?? false
      },

      isAtLeast: (role) => {
        const user = get().user
        if (!user) return false
        return (ROLE_LEVEL[user.role] ?? 0) >= (ROLE_LEVEL[role] ?? 0)
      },
    }),
    {
      name: 'ipa-auth',
      partialize: (state) => ({ token: state.token }),
    },
  ),
)

/** Hook that initializes the auth state by fetching /api/auth/me on mount. */
export const useAuth = () => {
  const store = useAuthStore()

  useEffect(() => {
    if (store.token && !store.isInitialized) {
      store.setUser(store.user!) // Trigger loading state
      authApi
        .getMe()
        .then((user) => store.setUser(user))
        .catch(() => {
          store.logout()
        })
    } else if (!store.token) {
      useAuthStore.setState({ isInitialized: true })
    }
  }, [store.token])

  return {
    token: store.token,
    user: store.user,
    isLoading: store.isLoading,
    isInitialized: store.isInitialized,
    isAuthenticated: !!store.token && !!store.user,
    setToken: store.setToken,
    setUser: store.setUser,
    logout: store.logout,
    hasPermission: store.hasPermission,
    isAtLeast: store.isAtLeast,
  }
}
