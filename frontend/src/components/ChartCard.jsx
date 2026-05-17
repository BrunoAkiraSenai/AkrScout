export function ChartCard({ title, subtitle, children, action }) {
  return (
    <div className="rounded-xl border border-slate-800/60 bg-slate-900/50 p-5 transition-all duration-300 hover:border-slate-700/60 hover:shadow-lg hover:shadow-slate-900/50">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
          {subtitle && (
            <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      {children}
    </div>
  )
}
