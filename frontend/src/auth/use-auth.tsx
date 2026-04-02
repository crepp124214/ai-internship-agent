import { createContext, useContext } from 'react'

export type AuthUser = {
  id: number
  username: string
  email: string
  name: string
  phone: string | null
  bio: string | null
  avatar_url: string | null
  created_at: string
  updated_at: string
}

export type AuthContextValue = {
  token: string | null
  user: AuthUser | null
  isBootstrapping: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshCurrentUser: () => Promise<void>
  refreshToken: () => Promise<string | void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)

  if (!value) {
    throw new Error('useAuth must be used within an AuthContext provider')
  }

  return value
}
