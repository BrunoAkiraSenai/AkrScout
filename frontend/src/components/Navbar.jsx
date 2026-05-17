import { Search, Bell, Settings, LogOut } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'

export function Navbar() {
  const { t } = useTranslation()
  const { user, signOut } = useAuth()
  const displayName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800/60 bg-slate-950/60 backdrop-blur-xl md:px-6">
      <div className="ml-14 flex-1 md:ml-0 md:max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder={t('navbar.search_placeholder')}
            className="w-full rounded-lg border border-slate-800/60 bg-slate-900/50 py-2 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-500 outline-none transition-all duration-200 focus:border-indigo-500/50 focus:bg-slate-900 focus:ring-1 focus:ring-indigo-500/20"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 pr-4 md:pr-0">
        <button className="relative rounded-lg p-2 text-slate-400 transition-all duration-200 hover:bg-slate-800/50 hover:text-slate-200">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 animate-pulse rounded-full bg-rose-500 ring-2 ring-slate-950" />
        </button>
        <button className="rounded-lg p-2 text-slate-400 transition-all duration-200 hover:bg-slate-800/50 hover:text-slate-200">
          <Settings className="h-4 w-4" />
        </button>
        <button
          onClick={signOut}
          className="rounded-lg p-2 text-slate-400 transition-all duration-200 hover:bg-rose-500/10 hover:text-rose-400"
          title={t('navbar.sign_out_title')}
        >
          <LogOut className="h-4 w-4" />
        </button>
        <div className="ml-2 hidden items-center gap-3 border-l border-slate-800/60 pl-3 sm:flex">
          <div className="text-right">
            <p className="max-w-28 truncate text-xs font-medium text-slate-200">
              {displayName}
            </p>
            <p className="text-[10px] text-slate-500">{t('navbar.pro_plan')}</p>
          </div>
          <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-indigo-400 to-violet-600 ring-2 ring-slate-800" />
        </div>
      </div>
    </header>
  )
}
