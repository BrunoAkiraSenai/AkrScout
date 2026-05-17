import { cn } from '../lib/utils'

const filterOptions = [
  { key: 'remote', label: 'Remote', value: true },
  { key: 'seniority', label: 'Junior', value: 'junior' },
  { key: 'seniority', label: 'Mid', value: 'mid' },
  { key: 'seniority', label: 'Senior', value: 'senior' },
  { key: 'employment_type', label: 'Full-Time', value: 'full_time' },
  { key: 'employment_type', label: 'Contract', value: 'contract' },
]

export function FilterPanel({ activeFilters, onFilterChange, onClear, hasFilters }) {
  function isActive(opt) {
    return activeFilters[opt.key] === opt.value
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {filterOptions.map((opt) => (
        <button
          key={`${opt.key}-${opt.value}`}
          onClick={() =>
            onFilterChange(opt.key, isActive(opt) ? null : opt.value)
          }
          className={cn(
            'rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all duration-200',
            isActive(opt)
              ? 'bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/30'
              : 'bg-slate-900/50 text-slate-400 ring-1 ring-slate-800/60 hover:bg-slate-800/50 hover:text-slate-300'
          )}
        >
          {opt.label}
        </button>
      ))}
      {hasFilters && (
        <button
          onClick={onClear}
          className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:text-slate-300"
        >
          Clear all
        </button>
      )}
    </div>
  )
}
