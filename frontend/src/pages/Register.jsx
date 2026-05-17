import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useSEO } from '../hooks/useSEO'
import { useNotification } from '../contexts/NotificationContext'
import { AlertCircle, Loader2, CheckCircle2, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Register() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, signUp, error, clearError } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [confirmed, setConfirmed] = useState(false)
  const notification = useNotification()
  useSEO({ title: t('register.title') })

  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true })
  }, [user, navigate])

  useEffect(() => {
    return () => clearError()
  }, [clearError])

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    const { data, error } = await signUp(email, password)
    if (!error && data?.user && !data?.session) {
      setConfirmed(true)
      notification.success(t('register.success'))
    }
    if (error) notification.error(error.message)
    setSubmitting(false)
  }

  if (confirmed) {
    return (
      <div className="space-y-6">
        <div className="space-y-2 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
            <CheckCircle2 className="h-6 w-6 text-emerald-400" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            {t('register.confirmed_heading')}
          </h1>
          <p className="text-sm text-slate-500">
            {t('register.confirmed_description')}{' '}
            <span className="font-medium text-slate-300">{email}</span>
          </p>
        </div>
        <p className="text-center text-xs text-slate-500">
          <Link
            to="/login"
            className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
          >
            {t('register.back_to_signin')}
          </Link>
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          {t('register.heading')}
        </h1>
        <p className="text-sm text-slate-500">
          {t('register.description')}
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
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-400">
              {t('register.first_name')}
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('register.first_name_placeholder')}
              className="w-full rounded-lg border border-slate-800/60 bg-slate-900/50 px-3.5 py-2.5 text-sm text-slate-200 placeholder-slate-600 outline-none transition-all duration-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-400">
              {t('register.last_name')}
            </label>
            <input
              type="text"
              placeholder={t('register.last_name_placeholder')}
              className="w-full rounded-lg border border-slate-800/60 bg-slate-900/50 px-3.5 py-2.5 text-sm text-slate-200 placeholder-slate-600 outline-none transition-all duration-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-400">{t('register.email_label')}</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('register.email_placeholder')}
            required
            className="w-full rounded-lg border border-slate-800/60 bg-slate-900/50 px-3.5 py-2.5 text-sm text-slate-200 placeholder-slate-600 outline-none transition-all duration-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-400">
            {t('register.password_label')}
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('register.password_placeholder')}
            required
            minLength={6}
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
          disabled={submitting}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/30 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t('register.submitting')}
            </>
          ) : (
            t('register.submit')
          )}
        </button>
      </form>

      <p className="text-center text-xs text-slate-500">
        {t('register.has_account')}{' '}
        <Link
          to="/login"
          className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
        >
          {t('register.sign_in')}
        </Link>
      </p>
    </div>
  )
}
