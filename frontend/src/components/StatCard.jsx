import { cn } from '../lib/utils'

export function StatCard({ icon: Icon, label, value, trend, trendUp }) {
  return (
    <div className="group relative overflow-hidden rounded-xl border border-slate-800/60 bg-slate-900/50 p-5 transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80 hover:shadow-lg hover:shadow-slate-900/50">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.03] to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="relative flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            {label}
          </p>
          <p className="text-2xl font-bold tracking-tight text-slate-100">
            {value}
          </p>
          {trend && (
            <div className="flex items-center gap-1.5">
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 text-xs font-medium',
                  trendUp ? 'text-emerald-400' : 'text-rose-400'
                )}
              >
                {trendUp ? '↑' : '↓'} {trend}
              </span>
              <span className="text-xs text-slate-600">vs last month</span>
            </div>
          )}
        </div>
        <div className="rounded-lg bg-indigo-500/10 p-2.5 ring-1 ring-indigo-500/20 transition-all duration-300 group-hover:bg-indigo-500/20 group-hover:ring-indigo-500/30">
          <Icon className="h-5 w-5 text-indigo-400" />
        </div>
      </div>
    </div>
  )
}
