import { cn } from '../lib/utils'

export function Skeleton({ className, variant = 'card', count = 1 }) {
  if (variant === 'card') {
    return (
      <div className={cn('space-y-3', className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="animate-shimmer rounded-xl border border-slate-800/40 bg-slate-900/30 p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/5 rounded-md bg-slate-800/60" />
                <div className="h-3 w-2/5 rounded-md bg-slate-800/40" />
                <div className="h-3 w-1/3 rounded-md bg-slate-800/30" />
              </div>
              <div className="h-8 w-8 rounded-lg bg-slate-800/40" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'stat') {
    return (
      <div className={cn('grid gap-4 sm:grid-cols-2 xl:grid-cols-4', className)}>
        {Array.from({ length: count || 4 }).map((_, i) => (
          <div key={i} className="animate-shimmer rounded-xl border border-slate-800/40 bg-slate-900/30 p-5">
            <div className="space-y-3">
              <div className="h-3 w-16 rounded-md bg-slate-800/50" />
              <div className="h-7 w-24 rounded-md bg-slate-800/60" />
              <div className="h-3 w-20 rounded-md bg-slate-800/30" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'chart') {
    return (
      <div className={cn('grid gap-6 lg:grid-cols-2', className)}>
        {Array.from({ length: count || 2 }).map((_, i) => (
          <div key={i} className="animate-shimmer rounded-xl border border-slate-800/40 bg-slate-900/30 p-5">
            <div className="mb-4 space-y-1">
              <div className="h-4 w-32 rounded-md bg-slate-800/60" />
              <div className="h-3 w-24 rounded-md bg-slate-800/30" />
            </div>
            <div className="h-64 rounded-lg bg-slate-800/20" />
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'text') {
    return (
      <div className={cn('animate-shimmer space-y-2', className)}>
        {Array.from({ length: count || 3 }).map((_, i) => (
          <div key={i} className="h-3 w-full rounded bg-slate-800/40" style={{ width: `${70 + Math.random() * 30}%` }} />
        ))}
      </div>
    )
  }

  return null
}

export function PageSkeleton() {
  return (
    <div className="animate-fade-in space-y-6">
      <div className="animate-shimmer space-y-2">
        <div className="h-7 w-40 rounded-md bg-slate-800/60" />
        <div className="h-4 w-56 rounded-md bg-slate-800/30" />
      </div>
      <Skeleton variant="stat" />
      <Skeleton variant="chart" />
    </div>
  )
}
