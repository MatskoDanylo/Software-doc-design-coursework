import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi } from '../api/auth'
import { onSessionExpired, refreshSession } from '../api/client'
import { tokens } from '../api/tokens'
import { usersApi } from '../api/users'
import type { LoginRequest, RegisterRequest } from '../types/auth'
import type { User } from '../types/user'
import { AuthContext, type AuthContextValue, type AuthStatus } from './context'

async function restoreSession(): Promise<User | null> {
  if (!(await refreshSession())) return null
  try {
    return await usersApi.me()
  } catch {
    return null
  }
}

export default function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>(() => (tokens.getRefresh() ? 'loading' : 'guest'))

  const logout = useCallback(() => {
    tokens.clear()
    setUser(null)
    setStatus('guest')
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    onSessionExpired(logout)
    return () => onSessionExpired(null)
  }, [logout])

  useEffect(() => {
    if (!tokens.getRefresh()) return
    let active = true
    restoreSession().then((restored) => {
      if (!active) return
      setUser(restored)
      setStatus(restored ? 'authenticated' : 'guest')
      if (restored) void queryClient.invalidateQueries()
    })
    return () => {
      active = false
    }
  }, [queryClient])

  const login = useCallback(
    async (data: LoginRequest) => {
      tokens.save(await authApi.login(data))
      const me = await usersApi.me()
      setUser(me)
      setStatus('authenticated')
      void queryClient.invalidateQueries()
      return me
    },
    [queryClient],
  )

  const register = useCallback(
    async (data: RegisterRequest) => {
      await authApi.register(data)
      return login({ email: data.email, password: data.password })
    },
    [login],
  )

  const refreshUser = useCallback(async () => {
    const me = await usersApi.me()
    setUser(me)
    return me
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, register, logout, updateUser: setUser, refreshUser }),
    [user, status, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
