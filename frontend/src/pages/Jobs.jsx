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

const MemoJobCard = memo(JobCard)

export default function Jobs() {
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
      added ? 'Job saved to favorites' : 'Job removed from favorites'
    )
  }

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          Jobs
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {count > 0
            ? `${count} positions found`
            : 'Browse and scout tech positions'}
        </p>
      </div>

      <SearchBar
        placeholder="Search by title or company..."
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
          title="No jobs found"
          description={
            hasFilters
              ? 'Try adjusting your filters or search terms'
              : 'No jobs have been scraped yet. Run the scraping pipeline first.'
          }
          action={
            hasFilters ? (
              <button
                onClick={clearFilters}
                className="rounded-lg bg-slate-800/50 px-4 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50"
              >
                Clear filters
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
                Page {page} of {totalPages} ({count} results)
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
