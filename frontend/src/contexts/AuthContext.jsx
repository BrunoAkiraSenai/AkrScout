import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { supabase } from '../services/supabase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = useCallback(async (email, password) => {
    setError(null)
    const { data, error: err } = await supabase.auth.signInWithPassword({ email, password })
    if (err) setError(err.message)
    return { data, error: err }
  }, [])

  const signUp = useCallback(async (email, password, name) => {
    setError(null)
    const { data, error: err } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: name },
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (err) setError(err.message)
    return { data, error: err }
  }, [])

  const signOut = useCallback(async () => {
    setError(null)
    const { error } = await supabase.auth.signOut()
    if (error) setError(error.message)
  }, [])

  const signInWithOAuth = useCallback(async (provider) => {
    setError(null)
    const { data, error: err } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
    if (err) setError(err.message)
    return { data, error: err }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        error,
        signIn,
        signUp,
        signOut,
        signInWithOAuth,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
