import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useSEO } from '../hooks/useSEO'
import { useNotification } from '../contexts/NotificationContext'
import { AlertCircle, Loader2, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Login() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, signIn, error, clearError, loading } = useAuth()
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

      <button
        type="button"
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-xs text-slate-500 transition-colors hover:text-indigo-400"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Voltar
      </button>

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
