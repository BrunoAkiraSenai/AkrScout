import { useEffect } from 'react'

export function useSEO({ title, description } = {}) {
  useEffect(() => {
    const prevTitle = document.title
    const prevDesc = document.querySelector('meta[name="description"]')
    const prevOgTitle = document.querySelector('meta[property="og:title"]')
    const prevOgDesc = document.querySelector('meta[property="og:description"]')
    const prevOgUrl = document.querySelector('meta[property="og:url"]')

    const base = 'AkrScout'
    document.title = title ? `${title} · ${base}` : base

    if (description) {
      setMeta('description', description)
      setMeta('og:description', description)
    }
    if (title) setMeta('og:title', `${title} · ${base}`)
    setMeta('og:url', window.location.href)

    return () => {
      document.title = prevTitle
      if (prevDesc) prevDesc.setAttribute('content', prevDesc.getAttribute('content') || '')
      if (prevOgTitle) prevOgTitle.setAttribute('content', prevOgTitle.getAttribute('content') || '')
      if (prevOgDesc) prevOgDesc.setAttribute('content', prevOgDesc.getAttribute('content') || '')
      if (prevOgUrl) prevOgUrl.setAttribute('content', prevOgUrl.getAttribute('content') || '')
    }
  }, [title, description])
}

function setMeta(name, content) {
  const attr = name.startsWith('og:') ? 'property' : 'name'
  let el = document.querySelector(`meta[${attr}="${name}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, name)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}
