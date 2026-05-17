import { Navigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'

function LoadingScreen() {
  const { t } = useTranslation()
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex h-12 w-12 items-center justify-center">
          <div className="absolute h-full w-full animate-spin rounded-full border-2 border-slate-800 border-t-indigo-500" />
          <div className="h-3 w-3 rounded-full bg-indigo-500/40" />
        </div>
        <div className="flex flex-col items-center gap-1">
          <p className="text-sm font-medium text-slate-400">{t('protected.loading_title')}</p>
          <p className="text-xs text-slate-600">{t('protected.loading_subtitle')}</p>
        </div>
      </div>
    </div>
  )
}

export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingScreen />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />

  return children
}
