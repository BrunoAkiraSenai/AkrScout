import {
  Briefcase,
  Monitor,
  Building2,
  Sparkles,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useAnalytics } from '../hooks/useAnalytics'
import { useSEO } from '../hooks/useSEO'
import { StatCard } from '../components/StatCard'
import { ChartCard } from '../components/ChartCard'
import { PageSkeleton } from '../components/Skeleton'
import { ErrorState } from '../components/ErrorState'
import { formatNumber } from '../lib/utils'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload) return null
  return (
    <div className="rounded-lg border border-slate-700/60 bg-slate-900/95 px-3 py-2 shadow-xl backdrop-blur-sm">
      <p className="text-xs font-medium text-slate-400">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-sm font-semibold" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const { topSkills, topCompanies, remoteStats, loading, error, refetch } = useAnalytics()
  useSEO({ title: 'Dashboard' })

  if (error) return <ErrorState message={error} onRetry={refetch} />
  if (loading) return <PageSkeleton />

  const totalJobs = remoteStats?.total_jobs || 0
  const remoteJobs = remoteStats?.remote_jobs || 0
  const companiesCount = topCompanies?.length || 0
  const skillsCount = topSkills?.length || 0

  const chartData = (topSkills || []).slice(0, 8)

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Overview of your scouting activity
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Briefcase}
          label="Total Jobs"
          value={formatNumber(totalJobs)}
          trend={remoteStats?.remote_percentage ? `Remote: ${remoteStats.remote_percentage}%` : null}
          trendUp
        />
        <StatCard
          icon={Monitor}
          label="Remote Jobs"
          value={formatNumber(remoteJobs)}
          trend={`${totalJobs ? ((remoteJobs / totalJobs) * 100).toFixed(0) : 0}%`}
          trendUp
        />
        <StatCard
          icon={Building2}
          label="Companies"
          value={formatNumber(companiesCount)}
          trend="active"
          trendUp
        />
        <StatCard
          icon={Sparkles}
          label="Skills Tracked"
          value={formatNumber(skillsCount)}
          trend="in demand"
          trendUp
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Top Skills in Demand" subtitle="By number of job listings">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#475569" tick={{ fontSize: 11 }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#475569"
                  tick={{ fontSize: 11 }}
                  width={70}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="demand_count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard title="Companies Hiring" subtitle="Most active employers">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={(topCompanies || []).slice(0, 8)}
                layout="vertical"
                margin={{ left: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#475569" tick={{ fontSize: 11 }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#475569"
                  tick={{ fontSize: 11 }}
                  width={80}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="job_count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      <div className="rounded-xl border border-slate-800/60 bg-slate-900/50 p-5 transition-all duration-300 hover:border-slate-700/60">
        <h3 className="text-sm font-semibold text-slate-200">
          Market Overview
        </h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-slate-800/30 p-4 transition-all duration-200 hover:bg-slate-800/50">
            <p className="text-xs text-slate-500">Remote Jobs</p>
            <p className="mt-1 text-2xl font-bold text-slate-100">
              {remoteStats?.remote_percentage ?? 0}%
            </p>
            <p className="mt-1 text-xs text-slate-600">of all listings</p>
          </div>
          <div className="rounded-lg bg-slate-800/30 p-4 transition-all duration-200 hover:bg-slate-800/50">
            <p className="text-xs text-slate-500">On-site Jobs</p>
            <p className="mt-1 text-2xl font-bold text-slate-100">
              {remoteStats?.remote_percentage
                ? (100 - remoteStats.remote_percentage).toFixed(1)
                : 0}%
            </p>
            <p className="mt-1 text-xs text-slate-600">of all listings</p>
          </div>
          <div className="rounded-lg bg-slate-800/30 p-4 transition-all duration-200 hover:bg-slate-800/50">
            <p className="text-xs text-slate-500">Active Listings</p>
            <p className="mt-1 text-2xl font-bold text-slate-100">
              {remoteStats?.active_remote_jobs ?? 0}
            </p>
            <p className="mt-1 text-xs text-slate-600">currently open</p>
          </div>
        </div>
      </div>
    </div>
  )
}
