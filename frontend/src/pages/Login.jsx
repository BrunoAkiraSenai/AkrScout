import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useSEO } from '../hooks/useSEO'
import { useNotification } from '../contexts/NotificationContext'
import { AlertCircle, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Login() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, signIn, signInWithOAuth, error, clearError, loading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const notification = useNotification()
  useSEO({ title: t('login.title') })

  const from = location.state?.from?.pathname || '/dashboard'

  useEffect(() => {
    if (user) navigate(from, { replace: true })
  }, [user, navigate, from])

  useEffect(() => {
    return () => clearError()
  }, [clearError])

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    const { error } = await signIn(email, password)
    if (!error) {
      notification.success(t('login.welcome_back'))
      navigate(from, { replace: true })
    } else {
      notification.error(error.message)
    }
    setSubmitting(false)
  }

  async function handleOAuth(provider) {
    await signInWithOAuth(provider)
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          {t('login.heading')}
        </h1>
        <p className="text-sm text-slate-500">
          {t('login.description')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-400">{t('login.email_label')}</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('login.email_placeholder')}
            required
            className="w-full rounded-lg border border-slate-800/60 bg-slate-900/50 px-3.5 py-2.5 text-sm text-slate-200 placeholder-slate-600 outline-none transition-all duration-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-400">
              {t('login.password_label')}
            </label>
            <button
              type="button"
              className="text-[11px] text-slate-500 transition-colors hover:text-indigo-400"
            >
              {t('login.forgot')}
            </button>
          </div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            className="w-full rounded-lg border border-slate-800/60 bg-slate-900/50 px-3.5 py-2.5 text-sm text-slate-200 placeholder-slate-600 outline-none transition-all duration-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20"
          />
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-2">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-400" />
            <p className="text-xs text-rose-300">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/30 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t('login.submitting')}
            </>
          ) : (
            t('login.submit')
          )}
        </button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-800/60" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-slate-950 px-2 text-slate-500">
            {t('login.divider')}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => handleOAuth('google')}
          disabled={submitting}
          className="flex items-center justify-center gap-2 rounded-lg border border-slate-800/60 bg-slate-900/50 px-4 py-2.5 text-xs font-medium text-slate-300 transition-all duration-200 hover:bg-slate-800/50 disabled:opacity-50"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Google
        </button>
        <button
          onClick={() => handleOAuth('github')}
          disabled={submitting}
          className="flex items-center justify-center gap-2 rounded-lg border border-slate-800/60 bg-slate-900/50 px-4 py-2.5 text-xs font-medium text-slate-300 transition-all duration-200 hover:bg-slate-800/50 disabled:opacity-50"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24">
            <path fill="currentColor" d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.39.6.11.82-.26.82-.58 0-.28-.01-1.04-.02-2.05-3.33.72-4.03-1.6-4.03-1.6-.54-1.38-1.33-1.75-1.33-1.75-1.09-.74.08-.73.08-.73 1.2.09 1.83 1.23 1.83 1.23 1.07 1.83 2.8 1.3 3.49.99.11-.77.42-1.3.76-1.6-2.66-.3-5.46-1.33-5.46-5.93 0-1.31.47-2.38 1.23-3.22-.12-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23.96-.27 1.98-.4 3-.41 1.02.01 2.04.14 3 .41 2.3-1.55 3.3-1.23 3.3-1.23.66 1.66.24 2.88.12 3.18.76.84 1.23 1.91 1.23 3.22 0 4.61-2.8 5.63-5.48 5.93.43.37.82 1.1.82 2.22 0 1.6-.02 2.89-.02 3.28 0 .32.22.7.83.58C20.56 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
          GitHub
        </button>
      </div>

      <p className="text-center text-xs text-slate-500">
        {t('login.no_account')}{' '}
        <Link
          to="/register"
          className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
        >
          {t('login.sign_up')}
        </Link>
      </p>
    </div>
  )
}
