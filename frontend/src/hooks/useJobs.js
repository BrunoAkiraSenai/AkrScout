import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../services/supabase'

const PAGE_SIZE = 12

export function useJobs() {
  const [jobs, setJobs] = useState([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({
    remote: null,
    seniority: null,
    source: null,
  })

  const hasFilters = search || filters.remote !== null || filters.seniority || filters.source

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      let query = supabase
        .from('vw_jobs')
        .select('*', { count: 'exact' })
        .eq('status', 'active')
        .order('scraped_at', { ascending: false })
        .range((page - 1) * PAGE_SIZE, page * PAGE_SIZE - 1)

      if (search) {
        query = query.or(
          `title.ilike.%${search}%,company_name.ilike.%${search}%`
        )
      }
      if (filters.remote === true || filters.remote === false) {
        query = query.eq('remote', filters.remote)
      }
      if (filters.seniority) {
        query = query.eq('seniority', filters.seniority)
      }
      if (filters.source) {
        query = query.eq('source', filters.source)
      }

      const { data, count: total, error: err } = await query

      if (err) throw err
      setJobs(data || [])
      setCount(total || 0)
    } catch (err) {
      setError(err.message)
      setJobs([])
      setCount(0)
    } finally {
      setLoading(false)
    }
  }, [page, search, filters])

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE))

  const setFilter = useCallback((key, value) => {
    setPage(1)
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  const clearFilters = useCallback(() => {
    setPage(1)
    setSearch('')
    setFilters({ remote: null, seniority: null, source: null })
  }, [])

  return {
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
    refetch: fetchJobs,
  }
}
