import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../services/supabase'
import { useAuth } from './useAuth'

export function useFavorites() {
  const { user } = useAuth()
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const [favoriteIds, setFavoriteIds] = useState(new Set())

  const fetchFavorites = useCallback(async () => {
    if (!user) {
      setFavorites([])
      setFavoriteIds(new Set())
      setLoading(false)
      return
    }

    try {
      const { data: favs } = await supabase
        .from('favorites')
        .select('id, job_id, created_at')
        .eq('user_id', user.id)

      const ids = (favs || []).map((f) => f.job_id)
      setFavoriteIds(new Set(ids))

      if (ids.length > 0) {
        const { data: jobs } = await supabase
          .from('vw_jobs')
          .select('*')
          .in('id', ids)

        const merged = (jobs || []).map((job) => ({
          ...job,
          favorite_id: favs.find((f) => f.job_id === job.id)?.id,
          favorited_at: favs.find((f) => f.job_id === job.id)?.created_at,
        }))
        setFavorites(merged)
      } else {
        setFavorites([])
      }
    } catch {
      setFavorites([])
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchFavorites()
  }, [fetchFavorites])

  const toggle = useCallback(
    async (jobId) => {
      if (!user) return false

      if (favoriteIds.has(jobId)) {
        const existing = favorites.find((f) => f.id === jobId)
        const favId = existing?.favorite_id

        if (favId) {
          await supabase.from('favorites').delete().eq('id', favId)
        } else {
          await supabase
            .from('favorites')
            .delete()
            .eq('user_id', user.id)
            .eq('job_id', jobId)
        }

        setFavoriteIds((prev) => {
          const next = new Set(prev)
          next.delete(jobId)
          return next
        })
        setFavorites((prev) => prev.filter((f) => f.id !== jobId))
        return false
      }

      const { data } = await supabase
        .from('favorites')
        .insert({ user_id: user.id, job_id: jobId })
        .select('id')
        .single()

      if (data) {
        setFavoriteIds((prev) => new Set(prev).add(jobId))
        await fetchFavorites()
      }
      return true
    },
    [user, favoriteIds, favorites, fetchFavorites]
  )

  const isFavorited = useCallback(
    (jobId) => favoriteIds.has(jobId),
    [favoriteIds]
  )

  return { favorites, favoriteIds, loading, toggle, isFavorited, refetch: fetchFavorites }
}
