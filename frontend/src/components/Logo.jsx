export function Logo({ size = 'sm', showText = true }) {
  const sizes = {
    sm: { box: 'h-8 w-8', icon: 'h-4 w-4', text: 'text-sm' },
    md: { box: 'h-10 w-10', icon: 'h-5 w-5', text: 'text-base' },
    lg: { box: 'h-12 w-12', icon: 'h-6 w-6', text: 'text-lg' },
  }
  const s = sizes[size] || sizes.sm
  return (
    <div className="flex items-center gap-3">
      <div className={`flex ${s.box} items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20`}>
        <svg className={`${s.icon} text-white`} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="10" cy="10" r="6" opacity="0.7" />
          <line x1="14" y1="14" x2="18" y2="18" />
        </svg>
      </div>
      {showText && <span className={`${s.text} font-bold tracking-tight text-slate-100`}>AkrScout</span>}
    </div>
  )
}
