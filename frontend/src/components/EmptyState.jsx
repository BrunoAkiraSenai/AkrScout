import { cn } from '../lib/utils'

export function EmptyState({ icon: Icon, title, description, action, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-20', className)}>
      {Icon && (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800/40 ring-1 ring-slate-700/40">
          <Icon className="h-6 w-6 text-slate-500" />
        </div>
      )}
      <p className="text-sm font-semibold text-slate-400">{title}</p>
      {description && (
        <p className="mt-1 max-w-xs text-center text-xs text-slate-600">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
