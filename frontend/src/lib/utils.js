export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}

export function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toLocaleString()
}

export function formatDate(date, locale = 'pt-BR') {
  return new Intl.RelativeTimeFormat(locale, { numeric: 'auto' }).format(
    -Math.round((Date.now() - new Date(date).getTime()) / 86400000),
    'day'
  )
}
