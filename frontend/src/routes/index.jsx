import { useTranslation } from 'react-i18next'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '../hooks/useTheme'
import { AuthProvider } from '../contexts/AuthContext'
import { NotificationProvider } from '../contexts/NotificationContext'
import { AppLayout } from '../components/layouts/AppLayout'
import { AuthLayout } from '../components/layouts/AuthLayout'
import { ProtectedRoute } from '../components/ProtectedRoute'

import Home from '../pages/Home'
import Dashboard from '../pages/Dashboard'
import Jobs from '../pages/Jobs'
import Analytics from '../pages/Analytics'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Favorites from '../pages/Favorites'

export function AppRoutes() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <NotificationProvider>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route element={<AppLayout />}>
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/jobs"
                element={
                  <ProtectedRoute>
                    <Jobs />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analytics"
                element={
                  <ProtectedRoute>
                    <Analytics />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/favorites"
                element={
                  <ProtectedRoute>
                    <Favorites />
                  </ProtectedRoute>
                }
              />
            </Route>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Route>
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </NotificationProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

function AuthCallback() {
  const { t } = useTranslation()
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex h-10 w-10 items-center justify-center">
          <div className="absolute h-full w-full animate-spin rounded-full border-2 border-slate-800 border-t-indigo-500" />
          <div className="h-3 w-3 rounded-full bg-indigo-500/30" />
        </div>
        <p className="text-xs text-slate-500">{t('auth_callback.message')}</p>
      </div>
    </div>
  )
}
