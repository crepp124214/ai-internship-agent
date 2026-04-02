import type { PropsWithChildren } from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { authApi, readApiError } from '../lib/api'
import type { TokenResponse } from '../lib/api'
import {
  getStoredToken,
  setStoredToken,
  setStoredTokens,
  getStoredRefreshToken,
  clearStoredTokens,
} from './auth-storage'
import { AuthContext, type AuthUser } from './use-auth'

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => getStoredToken())
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // ignore
    } finally {
      clearStoredTokens()
      setToken(null)
      setUser(null)
      // Optional: redirect to login route
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
  }, [])

  const refreshCurrentUser = useCallback(async () => {
    const activeToken = getStoredToken()

    if (!activeToken) {
      setToken(null)
      setUser(null)
      return
    }

    try {
      const currentUser = await authApi.getCurrentUser()
      setToken(activeToken)
      setUser(currentUser)
    } catch {
      await logout()
      throw new Error('Unable to refresh current user')
    }
  }, [logout])

  const login = useCallback(
    async (username: string, password: string) => {
      try {
        const { access_token, refresh_token } = await authApi.login({ username, password }) as TokenResponse
        // Store both tokens for rotation
        if (refresh_token) {
          setStoredTokens(access_token, refresh_token)
        } else {
          // Fallback for compatibility: store access token only
          setStoredToken(access_token)
        }
        setToken(access_token)

        const currentUser = await authApi.getCurrentUser()
        setUser(currentUser)
      } catch (error) {
        await logout()
        throw new Error(readApiError(error))
      }
    },
    [logout],
  )

  // Token refresh helper
  const refreshToken = useCallback(async () => {
    const refresh = getStoredRefreshToken()
    if (!refresh) {
      await logout()
      throw new Error('No refresh token available')
    }

    const refreshed = await authApi.refreshToken()
    const { access_token: newAccess, refresh_token: newRefresh } = refreshed
    if (newAccess) {
      setStoredTokens(newAccess, newRefresh ?? refresh)
      setToken(newAccess)
      return newAccess
    }
    await logout()
    throw new Error('Failed to refresh token')
  }, [logout])

  useEffect(() => {
    async function bootstrap() {
      const activeToken = getStoredToken()

      if (!activeToken) {
        setIsBootstrapping(false)
        return
      }

      try {
        const currentUser = await authApi.getCurrentUser()
        setToken(activeToken)
        setUser(currentUser)
      } catch {
        // Token might be expired; try refreshing
        try {
          const newAccess = await refreshToken()
          // After refresh, try to fetch user again
          const currentUser = await authApi.getCurrentUser()
          setToken(newAccess)
          setUser(currentUser)
        } catch {
          await logout()
        }
      } finally {
        setIsBootstrapping(false)
      }
    }

    void bootstrap()
  }, [logout])

  const value = useMemo(
    () => ({
      token,
      user,
      isBootstrapping,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      refreshCurrentUser,
      refreshToken,
    }),
    [isBootstrapping, login, logout, refreshCurrentUser, refreshToken, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
