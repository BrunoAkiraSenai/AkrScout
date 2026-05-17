import { memo } from 'react'
import { useTranslation } from 'react-i18next'
import { Heart, MapPin, Clock, Building2, ExternalLink } from 'lucide-react'
import { formatDate } from '../lib/utils'

export const JobCard = memo(function JobCard({ job, favorited, onToggleFavorite }) {
  const { t } = useTranslation()
  const employmentLabels = {
    full_time: t('job.full_time'),
    part_time: t('job.part_time'),
    contract: t('job.contract'),
    internship: t('job.internship'),
    temporary: t('job.temporary'),
  }
  const salary =
    job.salary_min && job.salary_max
      ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
      : job.salary_min
        ? `From $${job.salary_min.toLocaleString()}`
        : null

  return (
    <div className="group rounded-xl border border-slate-800/60 bg-slate-900/50 p-4 transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80 hover:shadow-lg hover:shadow-slate-900/50">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-200 transition-colors group-hover:text-indigo-400">
              {job.title}
            </h3>
            {job.employment_type && (
              <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400 ring-1 ring-emerald-500/20">
                {employmentLabels[job.employment_type] || job.employment_type}
              </span>
            )}
            {job.remote && (
              <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-[10px] font-medium text-indigo-400 ring-1 ring-indigo-500/20">
                {t('job.remote_badge')}
              </span>
            )}
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Building2 className="h-3 w-3" />
              {job.company_name}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {job.location || t('job.unknown_location')}
            </span>
            {job.posted_at && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDate(job.posted_at)}
              </span>
            )}
          </div>

          {salary && (
            <p className="mt-2 text-sm font-medium text-slate-300">{salary}</p>
          )}

          {job.skills?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {job.skills.map((skill) => (
                <span
                  key={skill.slug}
                  className="rounded-md bg-slate-800/60 px-2 py-0.5 text-[10px] font-medium text-slate-400"
                >
                  {skill.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onToggleFavorite?.(job.id)}
            className={`rounded-lg p-2 transition-colors ${
              favorited
                ? 'text-rose-400 hover:bg-rose-500/10'
                : 'text-slate-600 hover:bg-rose-500/10 hover:text-rose-400'
            }`}
          >
            <Heart className={`h-4 w-4 ${favorited ? 'fill-rose-400' : ''}`} />
          </button>
          {job.job_url && (
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-800/50 hover:text-slate-300"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
})
