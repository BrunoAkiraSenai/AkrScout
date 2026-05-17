import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useSEO } from '../hooks/useSEO'
import {
  ArrowRight,
  BarChart3,
  Briefcase,
  Crosshair,
  Heart,
  TrendingUp,
  Zap,
  Shield,
  Layers,
  ChevronRight,
  Star,
  Menu,
  X,
} from 'lucide-react'

import { useTranslation } from 'react-i18next'

const metrics = [
  { value: '12K+', label: t('home.metric_jobs') },
  { value: '850+', label: t('home.metric_companies') },
  { value: '40+', label: t('home.metric_skills') },
  { value: '95%', label: t('home.metric_accuracy') },
]

const features = [
  {
    icon: Crosshair,
    title: t('home.feature_scouting'),
    description: t('home.feature_scouting_desc'),
  },
  {
    icon: BarChart3,
    title: t('home.feature_analytics'),
    description: t('home.feature_analytics_desc'),
  },
  {
    icon: Heart,
    title: t('home.feature_favorites'),
    description: t('home.feature_favorites_desc'),
  },
  {
    icon: TrendingUp,
    title: t('home.feature_trends'),
    description: t('home.feature_trends_desc'),
  },
  {
    icon: Shield,
    title: t('home.feature_quality'),
    description: t('home.feature_quality_desc'),
  },
  {
    icon: Layers,
    title: t('home.feature_radar'),
    description: t('home.feature_radar_desc'),
  },
]

const testimonials = [
  { name: t('home.testimonial_1_name'), role: t('home.testimonial_1_role'), content: t('home.testimonial_1_content'), rating: 5 },
  { name: t('home.testimonial_2_name'), role: t('home.testimonial_2_role'), content: t('home.testimonial_2_content'), rating: 5 },
  { name: t('home.testimonial_3_name'), role: t('home.testimonial_3_role'), content: t('home.testimonial_3_content'), rating: 5 },
]

export default function Home() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [mobileMenu, setMobileMenu] = useState(false)
  useSEO({ title: 'Intelligent Job Scouting', description: 'Discover tech opportunities, track market trends, and land your next role with data-driven insights.' })
  const { t } = useTranslation()

  useEffect(() => {
    if (!loading && user) navigate('/dashboard', { replace: true })
  }, [user, loading, navigate])

  useEffect(() => {
    if (mobileMenu) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [mobileMenu])

  if (loading || user) return null

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Nav */}
      <nav className="fixed top-0 z-50 w-full border-b border-slate-800/40 bg-slate-950/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
              <Crosshair className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-100">AKR Scout</span>
          </div>
          <div className="hidden items-center gap-6 md:flex">
            <a href="#features" className="text-xs font-medium text-slate-400 transition-colors hover:text-slate-200">{t('nav.features')}</a>
            <a href="#metrics" className="text-xs font-medium text-slate-400 transition-colors hover:text-slate-200">{t('nav.metrics')}</a>
            <Link to="/login" className="text-xs font-medium text-slate-400 transition-colors hover:text-slate-200">{t('nav.sign_in')}</Link>
            <Link to="/register" className="rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/20 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/30">
              {t('nav.get_started')}
            </Link>
          </div>
          <button
            onClick={() => setMobileMenu(true)}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 md:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenu && (
        <div className="fixed inset-0 z-[60] bg-slate-950/98 backdrop-blur-xl md:hidden">
          <div className="flex h-16 items-center justify-between px-4">
            <span className="text-lg font-bold text-slate-100">AKR Scout</span>
            <button onClick={() => setMobileMenu(false)} className="text-slate-400">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex flex-col items-center gap-6 px-4 pt-12">
            <a href="#features" onClick={() => setMobileMenu(false)} className="text-sm font-medium text-slate-300">{t('nav.features')}</a>
            <a href="#metrics" onClick={() => setMobileMenu(false)} className="text-sm font-medium text-slate-300">{t('nav.metrics')}</a>
            <Link to="/login" onClick={() => setMobileMenu(false)} className="text-sm font-medium text-slate-300">{t('nav.sign_in')}</Link>
            <Link to="/register" onClick={() => setMobileMenu(false)} className="mt-4 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20">
              {t('nav.get_started')}
            </Link>
          </div>
        </div>
      )}

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-20 md:pt-40 md:pb-28">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_center,_var(--tw-gradient-stops))] from-indigo-900/15 via-transparent to-transparent" />
        <div className="absolute -top-40 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-indigo-500/5 blur-3xl" />
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/5 px-4 py-1">
              <Zap className="h-3 w-3 text-indigo-400" />
              <span className="text-[11px] font-medium text-indigo-300">{t('home.badge')}</span>
            </div>
            <h1 className="animate-fade-in-up text-4xl font-bold tracking-tight text-slate-100 md:text-6xl">
              {t('home.hero_title')}
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-sm leading-relaxed text-slate-400 md:text-base">
              {t('home.hero_subtitle')}
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                to="/register"
                className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/40 sm:w-auto"
              >
                {t('home.cta_start')}
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
              <a
                href="#features"
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700/60 bg-slate-900/50 px-6 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-slate-600/60 sm:w-auto"
              >
                {t('home.cta_learn')}
                <ChevronRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section id="metrics" className="border-y border-slate-800/40 py-12">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            {metrics.map((metric, i) => (
              <div key={metric.label} className={`animate-fade-in-up text-center stagger-${i + 1}`}>
                <p className="text-3xl font-bold text-slate-100 md:text-4xl">{metric.value}</p>
                <p className="mt-1 text-xs text-slate-500">{metric.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="mx-auto mb-16 max-w-2xl text-center">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
              {t('home.features_title')}
            </h2>
            <p className="mt-3 text-sm text-slate-400">
              {t('home.features_subtitle')}
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={`animate-fade-in-up group rounded-xl border border-slate-800/40 bg-slate-900/30 p-6 transition-all duration-300 hover:border-slate-700/50 hover:bg-slate-900/60 stagger-${i + 1}`}
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10 ring-1 ring-indigo-500/20 transition-all duration-300 group-hover:bg-indigo-500/20">
                  <feature.icon className="h-5 w-5 text-indigo-400" />
                </div>
                <h3 className="text-sm font-semibold text-slate-200">{feature.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="border-t border-slate-800/40 py-20">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
              {t('home.testimonials_title')}
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {testimonials.map((t) => (
              <div key={t.name} className="rounded-xl border border-slate-800/40 bg-slate-900/30 p-6">
                <div className="mb-3 flex gap-0.5">
                  {Array.from({ length: t.rating }).map((_, i) => (
                    <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="text-xs leading-relaxed text-slate-400">&ldquo;{t.content}&rdquo;</p>
                <div className="mt-4 flex items-center gap-3 border-t border-slate-800/40 pt-4">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-400 to-violet-600" />
                  <div>
                    <p className="text-xs font-medium text-slate-200">{t.name}</p>
                    <p className="text-[10px] text-slate-500">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-800/40 py-20">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="relative overflow-hidden rounded-2xl border border-slate-700/40 bg-gradient-to-br from-slate-900 via-indigo-950/30 to-slate-900 p-10 md:p-16">
            <div className="absolute -right-20 -top-20 h-60 w-60 rounded-full bg-indigo-500/5 blur-3xl" />
            <div className="relative mx-auto max-w-xl text-center">
              <h2 className="text-2xl font-bold tracking-tight text-slate-100 md:text-3xl">
                {t('home.cta_title')}
              </h2>
              <p className="mt-3 text-sm text-slate-400">
                {t('home.cta_subtitle')}
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                  to="/register"
                  className="group flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/40"
                >
                  {t('home.cta_free')}
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
                <Link
                  to="/login"
                  className="flex items-center justify-center gap-2 rounded-xl border border-slate-700/60 bg-slate-900/50 px-6 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-slate-600/60"
                >
                  {t('home.cta_signin')}
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/40 py-8">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-3">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-indigo-500 to-violet-600">
                <Crosshair className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="text-sm font-bold text-slate-200">AKR Scout</span>
            </div>
            <p className="text-xs text-slate-600">
              © {new Date().getFullYear()} AKR Scout. {t('home.footer')}
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
