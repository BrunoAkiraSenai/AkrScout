import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../services/supabase'

export function useAnalytics() {
  const [data, setData] = useState({
    topSkills: [],
    topCompanies: [],
    remoteStats: null,
    salaryBySeniority: [],
    jobsOverTime: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [skillsRes, companiesRes, remoteRes, salaryRes] =
        await Promise.all([
          supabase.from('vw_top_skills').select('*').limit(10),
          supabase.from('vw_top_companies').select('*').limit(10),
          supabase.from('vw_remote_stats').select('*').single(),
          supabase.from('vw_salary_by_seniority').select('*'),
        ])

      if (skillsRes.error) throw skillsRes.error
      if (companiesRes.error) throw companiesRes.error
      if (remoteRes.error) throw remoteRes.error
      if (salaryRes.error) throw salaryRes.error

      setData({
        topSkills: skillsRes.data || [],
        topCompanies: companiesRes.data || [],
        remoteStats: remoteRes.data,
        salaryBySeniority: salaryRes.data || [],
        jobsOverTime: [],
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  return { ...data, loading, error, refetch: fetchAll }
}
