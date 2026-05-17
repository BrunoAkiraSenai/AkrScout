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

const metrics = [
  { value: '12K+', label: 'Jobs Tracked' },
  { value: '850+', label: 'Companies' },
  { value: '40+', label: 'Skills Analyzed' },
  { value: '95%', label: 'Data Accuracy' },
]

const features = [
  {
    icon: Crosshair,
    title: 'Smart Scouting',
    description: 'Automated scraping from top tech job boards. Real-time updates on new opportunities.',
  },
  {
    icon: BarChart3,
    title: 'Market Analytics',
    description: 'Deep insights into salary trends, skill demand, and company hiring patterns.',
  },
  {
    icon: Heart,
    title: 'Smart Favorites',
    description: 'Save and organize promising positions. Never lose track of an opportunity.',
  },
  {
    icon: TrendingUp,
    title: 'Skill Trends',
    description: 'Discover which skills are in demand. Stay ahead of the market curve.',
  },
  {
    icon: Shield,
    title: 'Data Quality',
    description: 'Deduped, normalized, and enriched job data. No duplicates, no noise.',
  },
  {
    icon: Layers,
    title: 'Tech Radar',
    description: 'Comprehensive view of the tech landscape. From startups to big tech.',
  },
]

const testimonials = [
  { name: 'Alex M.', role: 'Senior Engineer', content: 'AKR Scout helped me track opportunities across 50+ companies. Landed my dream role in 3 weeks.', rating: 5 },
  { name: 'Sarah K.', role: 'Tech Recruiter', content: 'The analytics alone are worth it. I can see exactly what skills are trending in real-time.', rating: 5 },
  { name: 'David L.', role: 'Engineering Manager', content: 'Market intelligence at your fingertips. This is how job hunting should be done.', rating: 5 },
]

export default function Home() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [mobileMenu, setMobileMenu] = useState(false)
  useSEO({ title: 'Intelligent Job Scouting', description: 'Discover tech opportunities, track market trends, and land your next role with data-driven insights.' })

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
            <a href="#features" className="text-xs font-medium text-slate-400 transition-colors hover:text-slate-200">Features</a>
            <a href="#metrics" className="text-xs font-medium text-slate-400 transition-colors hover:text-slate-200">Metrics</a>
            <Link to="/login" className="text-xs font-medium text-slate-400 transition-colors hover:text-slate-200">Sign in</Link>
            <Link to="/register" className="rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/20 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/30">
              Get Started
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
            <a href="#features" onClick={() => setMobileMenu(false)} className="text-sm font-medium text-slate-300">Features</a>
            <a href="#metrics" onClick={() => setMobileMenu(false)} className="text-sm font-medium text-slate-300">Metrics</a>
            <Link to="/login" onClick={() => setMobileMenu(false)} className="text-sm font-medium text-slate-300">Sign in</Link>
            <Link to="/register" onClick={() => setMobileMenu(false)} className="mt-4 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20">
              Get Started
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
              <span className="text-[11px] font-medium text-indigo-300">Intelligent Job Scouting Platform</span>
            </div>
            <h1 className="animate-fade-in-up text-4xl font-bold tracking-tight text-slate-100 md:text-6xl">
              Never Miss a{' '}
              <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                Tech Opportunity
              </span>{' '}
              Again
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-sm leading-relaxed text-slate-400 md:text-base">
              AKR Scout automatically tracks thousands of tech jobs across the web.
              Get real-time market analytics, skill trends, and personalized job alerts.
              Your data-driven career compass.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                to="/register"
                className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/40 sm:w-auto"
              >
                Start Scouting Free
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
              <a
                href="#features"
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700/60 bg-slate-900/50 px-6 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-slate-600/60 sm:w-auto"
              >
                Learn More
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
              Everything you need to{' '}
              <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                scout smarter
              </span>
            </h2>
            <p className="mt-3 text-sm text-slate-400">
              From automated job tracking to deep market analytics — all in one platform.
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
              Trusted by{' '}
              <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                tech professionals
              </span>
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
                Ready to scout your next opportunity?
              </h2>
              <p className="mt-3 text-sm text-slate-400">
                Join thousands of tech professionals who use AKR Scout to stay ahead of the market.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                  to="/register"
                  className="group flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/40"
                >
                  Get Started Free
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
                <Link
                  to="/login"
                  className="flex items-center justify-center gap-2 rounded-xl border border-slate-700/60 bg-slate-900/50 px-6 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-slate-600/60"
                >
                  Sign In
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
              © {new Date().getFullYear()} AKR Scout. Intelligent job scouting platform.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
