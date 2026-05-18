import { memo } from 'react'
import { Heart, MapPin, Building2, Clock, ExternalLink } from 'lucide-react'
import { useFavorites } from '../hooks/useFavorites'
import { useSEO } from '../hooks/useSEO'
import { useNotification } from '../contexts/NotificationContext'
import { Skeleton } from '../components/Skeleton'
import { EmptyState } from '../components/EmptyState'
import { formatDate } from '../lib/utils'
import { useTranslation } from 'react-i18next'

const MemoFavoriteCard = memo(function FavoriteCard({ job, index, onToggle }) {
  const { t } = useTranslation()
  const salary =
    job.salary_min && job.salary_max
      ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
      : job.salary_min
        ? `From $${job.salary_min.toLocaleString()}`
        : null

  const labels = {
    full_time: t('job.full_time'),
    part_time: t('job.part_time'),
    contract: t('job.contract'),
    internship: t('job.internship'),
  }

  return (
    <div
      className="group animate-fade-in rounded-xl border border-slate-800/60 bg-slate-900/50 p-4 transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-200 transition-colors group-hover:text-indigo-400">
              {job.title}
            </h3>
            {job.employment_type && (
              <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400 ring-1 ring-emerald-500/20">
                {labels[job.employment_type] || job.employment_type}
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
              {job.location || t('favorites.unknown_location')}
            </span>
            {job.favorited_at && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {t('favorites.saved_prefix')} {formatDate(job.favorited_at)}
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
            onClick={() => onToggle(job.id)}
            className="rounded-lg p-2 text-rose-400 transition-colors hover:bg-rose-500/10"
          >
            <Heart className="h-4 w-4 fill-rose-400" />
          </button>
          {job.job_url && (
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-indigo-400"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {t('job.open_external')}
            </a>
          )}
        </div>
      </div>
    </div>
  )
})

export default function Favorites() {
  const { t } = useTranslation()
  const { favorites, loading, toggle } = useFavorites()
  const notification = useNotification()
  useSEO({ title: 'Favorites' })

  async function handleToggle(jobId) {
    const added = await toggle(jobId)
    if (!added) {
      notification.info(t('favorites.removed'))
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          {t('favorites.title')}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {favorites.length > 0
            ? t('favorites.subtitle_saved', { count: favorites.length })
            : t('favorites.subtitle_empty')}
        </p>
      </div>

      {loading ? (
        <Skeleton variant="card" count={2} />
      ) : favorites.length === 0 ? (
        <EmptyState
          icon={Heart}
          title={t('favorites.empty_title')}
          description={t('favorites.empty_description')}
        />
      ) : (
        <div className="space-y-3">
          {favorites.map((job, index) => (
            <MemoFavoriteCard
              key={job.id}
              job={job}
              index={index}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}
    </div>
  )
}
