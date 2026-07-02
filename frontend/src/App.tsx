import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { OAuthCallbackPage } from '@/pages/OAuthCallbackPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { EmailPage } from '@/pages/EmailPage'
import { CalendarPage } from '@/pages/CalendarPage'
import { AuditPage } from '@/pages/AuditPage'
import { AdminPage } from '@/pages/AdminPage'
import { AccountPage } from '@/pages/AccountPage'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<OAuthCallbackPage />} />

      {/* Protected — any authenticated user */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/email" element={<EmailPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/account" element={<AccountPage />} />

          {/* Manager + Admin only */}
          <Route element={<ProtectedRoute requiredRole="manager" />}>
            <Route path="/audit" element={<AuditPage />} />
          </Route>

          {/* Admin only */}
          <Route element={<ProtectedRoute requiredRole="admin" />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
