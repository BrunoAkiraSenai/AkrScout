import { AlertTriangle, RefreshCw } from 'lucide-react'
import { cn } from '../lib/utils'

export function ErrorState({ message, onRetry, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-20', className)}>
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 ring-1 ring-rose-500/20">
        <AlertTriangle className="h-6 w-6 text-rose-400" />
      </div>
      <p className="text-sm font-semibold text-slate-400">Something went wrong</p>
      {message && (
        <p className="mt-1 max-w-xs text-center text-xs text-slate-500">{message}</p>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 flex items-center gap-2 rounded-lg bg-slate-800/50 px-4 py-2 text-xs font-medium text-slate-300 transition-all duration-200 hover:bg-slate-700/50"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Try again
        </button>
      )}
    </div>
  )
}
