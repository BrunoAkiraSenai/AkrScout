import { Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Crosshair } from 'lucide-react'

export function AuthLayout() {
  const { t } = useTranslation()
  return (
    <div className="flex min-h-screen">
      <div className="relative hidden flex-1 flex-col justify-between bg-gradient-to-br from-slate-950 via-indigo-950/20 to-slate-950 p-12 lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-transparent to-transparent" />
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
              <Crosshair className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-100">
              AKR Scout
            </span>
          </div>
        </div>
        <div className="relative space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100">
              {t('auth.title')}
            </h2>
            <p className="text-sm leading-relaxed text-slate-400">
              {t('auth.description')}
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {[
              { value: '12K+', label: t('auth.stat_jobs') },
              { value: '850+', label: t('auth.stat_companies') },
              { value: '40+', label: t('auth.stat_skills') },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-slate-800/30 p-3 text-center">
                <p className="text-lg font-bold text-indigo-400">{stat.value}</p>
                <p className="text-[10px] text-slate-500">{stat.label}</p>
              </div>
            ))}
          </div>
          <blockquote className="border-l-2 border-indigo-500/30 pl-4">
            <p className="text-sm italic text-slate-400">
              {t('auth.quote')}
            </p>
            <div className="mt-2">
              <p className="text-xs font-medium text-slate-300">{t('auth.quote_author')}</p>
            </div>
          </blockquote>
        </div>
      </div>
      <div className="flex flex-1 items-center justify-center bg-slate-950 p-8">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center justify-center gap-3 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
              <Crosshair className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-100">
              AKR Scout
            </span>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
