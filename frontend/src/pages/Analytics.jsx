import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import { ChartCard } from '../components/ChartCard'
import { StatCard } from '../components/StatCard'
import { useAnalytics } from '../hooks/useAnalytics'
import { useSEO } from '../hooks/useSEO'
import { PageSkeleton } from '../components/Skeleton'
import { ErrorState } from '../components/ErrorState'
import { formatNumber } from '../lib/utils'
import { Briefcase, Monitor, Building2, Sparkles } from 'lucide-react'

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#e0e7ff']

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

export default function Analytics() {
  const {
    topSkills,
    topCompanies,
    remoteStats,
    salaryBySeniority,
    loading,
    error,
    refetch,
  } = useAnalytics()

  useSEO({ title: 'Analytics' })

  if (error) return <ErrorState message={error} onRetry={refetch} />
  if (loading) return <PageSkeleton />

  const totalJobs = remoteStats?.total_jobs || 0
  const skillsCount = topSkills?.length || 0
  const companiesCount = topCompanies?.length || 0
  const remotePercent = remoteStats?.remote_percentage || 0

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          Analytics
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Deep insights into your scouting data
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Briefcase}
          label="Total Listings"
          value={formatNumber(totalJobs)}
          trend="in database"
          trendUp
        />
        <StatCard
          icon={Monitor}
          label="Remote Rate"
          value={`${remotePercent}%`}
          trend="of all jobs"
          trendUp={remotePercent > 50}
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
          label="Skills"
          value={formatNumber(skillsCount)}
          trend="detected"
          trendUp
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Job Distribution" subtitle="Remote vs On-site">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[
                    { name: 'Remote', value: remoteStats?.remote_jobs || 0 },
                    {
                      name: 'On-site',
                      value: (remoteStats?.total_jobs || 0) - (remoteStats?.remote_jobs || 0),
                    },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  <Cell fill="#6366f1" />
                  <Cell fill="#1e293b" />
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard title="Salary by Seniority" subtitle="Average ranges per level">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={salaryBySeniority || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="seniority" stroke="#475569" tick={{ fontSize: 11 }} />
                <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="avg_salary_min"
                  fill="#6366f1"
                  radius={[4, 4, 0, 0]}
                  name="Avg Min"
                />
                <Bar
                  dataKey="avg_salary_max"
                  fill="#a78bfa"
                  radius={[4, 4, 0, 0]}
                  name="Avg Max"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Top Skills" subtitle="By job listing count">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={(topSkills || []).slice(0, 8)}
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
                <Bar dataKey="demand_count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard title="Top Companies" subtitle="By job listing count">
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
    </div>
  )
}
