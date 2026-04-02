import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AuthContext, type AuthContextValue } from './use-auth'
import { ProtectedRoute } from './protected-route'

function renderProtectedRoute(value: AuthContextValue, initialPath = '/dashboard') {
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/login" element={<div>login page</div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>dashboard page</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to login', () => {
    renderProtectedRoute({
      token: null,
      user: null,
      isBootstrapping: false,
      isAuthenticated: false,
      login: async () => undefined,
      logout: async () => undefined,
      refreshCurrentUser: async () => undefined,
      refreshToken: async () => {},
    })

    expect(screen.getByText('login page')).toBeInTheDocument()
  })

  it('renders children for authenticated users', () => {
    renderProtectedRoute({
      token: 'token-123',
      user: {
        id: 1,
        username: 'demo',
        email: 'demo@example.com',
        name: 'Demo User',
        phone: null,
        bio: null,
        avatar_url: null,
        created_at: '2026-03-29T00:00:00Z',
        updated_at: '2026-03-29T00:00:00Z',
      },
      isBootstrapping: false,
      isAuthenticated: true,
      login: async () => undefined,
      logout: async () => undefined,
      refreshCurrentUser: async () => undefined,
      refreshToken: async () => {},
    })

    expect(screen.getByText('dashboard page')).toBeInTheDocument()
  })
})
