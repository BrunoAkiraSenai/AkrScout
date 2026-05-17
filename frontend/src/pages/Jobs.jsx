import { memo } from 'react'
import { SearchBar } from '../components/SearchBar'
import { FilterPanel } from '../components/FilterPanel'
import { JobCard } from '../components/JobCard'
import { useJobs } from '../hooks/useJobs'
import { useFavorites } from '../hooks/useFavorites'
import { useSEO } from '../hooks/useSEO'
import { useNotification } from '../contexts/NotificationContext'
import { Skeleton } from '../components/Skeleton'
import { EmptyState } from '../components/EmptyState'
import { ChevronLeft, ChevronRight, Briefcase } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const MemoJobCard = memo(JobCard)

export default function Jobs() {
  const { t } = useTranslation()
  const {
    jobs,
    count,
    loading,
    error,
    page,
    totalPages,
    search,
    filters,
    hasFilters,
    setPage,
    setSearch,
    setFilter,
    clearFilters,
    refetch,
  } = useJobs()

  const { isFavorited, toggle } = useFavorites()
  const notification = useNotification()
  useSEO({ title: 'Jobs' })

  async function handleToggle(jobId) {
    const added = await toggle(jobId)
    notification[added ? 'success' : 'info'](
      added ? t('jobs.saved_favorites') : t('jobs.removed_favorites')
    )
  }

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          {t('jobs.title')}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {count > 0
            ? t('jobs.subtitle_count', { count })
            : t('jobs.subtitle_browse')}
        </p>
      </div>

      <SearchBar
        placeholder={t('jobs.search_placeholder')}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
      />
      <FilterPanel
        activeFilters={filters}
        onFilterChange={(key, value) => setFilter(key, value)}
        onClear={clearFilters}
        hasFilters={hasFilters}
      />

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3">
          <p className="text-xs text-rose-300">{error}</p>
        </div>
      )}

      {loading ? (
        <Skeleton variant="card" count={3} />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title={t('jobs.empty_title')}
          description={
            hasFilters
              ? t('jobs.empty_description_filters')
              : t('jobs.empty_description_no_data')
          }
          action={
            hasFilters ? (
              <button
                onClick={clearFilters}
                className="rounded-lg bg-slate-800/50 px-4 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50"
              >
                {t('jobs.clear_filters')}
              </button>
            ) : null
          }
        />
      ) : (
        <>
          <div className="space-y-3">
            {jobs.map((job) => (
              <MemoJobCard
                key={job.id}
                job={job}
                favorited={isFavorited(job.id)}
                onToggleFavorite={handleToggle}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-800/60 pt-4">
              <p className="text-xs text-slate-500">
                {t('jobs.page_of', { page, total: totalPages, count })}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1 || loading}
                  className="rounded-lg border border-slate-800/60 bg-slate-900/50 p-2 text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="min-w-[3rem] text-center text-xs text-slate-500">
                  {page}/{totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages || loading}
                  className="rounded-lg border border-slate-800/60 bg-slate-900/50 p-2 text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
