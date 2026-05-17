import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Briefcase,
  BarChart3,
  Heart,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { cn } from '../lib/utils'
import { useAuth } from '../hooks/useAuth'
import { Logo } from './Logo'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/favorites', label: 'Favorites', icon: Heart },
]

export function Sidebar({ collapsed, setCollapsed }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { user, signOut } = useAuth()
  const displayName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'
  const displayEmail = user?.email || ''

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  const sidebarContent = (
    <nav className="flex flex-1 flex-col">
      <div className="flex h-16 items-center border-b border-slate-800/60 px-4">
        <Logo size={collapsed ? 'sm' : 'md'} showText={!collapsed} />
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
        {links.map(({ to, label, icon: Icon }) => {
          const isActive = location.pathname === to
          return (
            <NavLink
              key={to}
              to={to}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-indigo-500/10 text-indigo-400 shadow-sm shadow-indigo-500/5'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{label}</span>}
              {isActive && !collapsed && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-500" />
              )}
            </NavLink>
          )
        })}
      </div>

      <div className="border-t border-slate-800/60 p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2">
          <div className="h-7 w-7 shrink-0 rounded-full bg-gradient-to-br from-indigo-400 to-violet-600" />
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-slate-200">{displayName}</p>
              <p className="truncate text-[10px] text-slate-500">{displayEmail}</p>
            </div>
          )}
        </div>
        <div className="mt-2 space-y-1">
          <button
            onClick={signOut}
            className="flex w-full items-center justify-center gap-2 rounded-lg p-1.5 text-xs text-slate-500 transition-colors hover:bg-rose-500/10 hover:text-rose-400"
          >
            <LogOut className="h-3.5 w-3.5 shrink-0" />
            {!collapsed && <span>Sign out</span>}
          </button>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden w-full items-center justify-center rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-slate-800/50 hover:text-slate-300 md:flex"
          >
            <svg className={cn('h-3.5 w-3.5 transition-transform duration-300', collapsed ? '' : 'rotate-180')} viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </nav>
  )

  return (
    <>
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-4 z-50 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900/80 text-slate-400 backdrop-blur-xl transition-colors hover:text-slate-200 md:hidden"
      >
        <Menu className="h-4 w-4" />
      </button>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-screen flex-col bg-slate-950/95 backdrop-blur-xl transition-all duration-300',
          'md:static md:z-40',
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
          collapsed ? 'md:w-16' : 'md:w-60'
        )}
      >
        {mobileOpen && (
          <button
            onClick={() => setMobileOpen(false)}
            className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 md:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        {sidebarContent}
      </aside>
    </>
  )
}
