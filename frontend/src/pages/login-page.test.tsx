import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextValue } from '../auth/use-auth'
import { LoginPage } from './login-page'

function renderLoginPage(value: AuthContextValue, initialEntry: string | { pathname: string; state?: unknown } = '/login') {
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/tracker" element={<div>tracker page</div>} />
          <Route path="/dashboard" element={<div>dashboard page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('LoginPage', () => {
  it('returns the user to their original protected route after login', async () => {
    const user = userEvent.setup()
    const login = vi.fn(async () => undefined)

    renderLoginPage(
      {
        token: null,
        user: null,
        isBootstrapping: false,
        isAuthenticated: false,
        login,
        logout: async () => undefined,
        refreshCurrentUser: async () => undefined,
        refreshToken: async () => undefined,
      },
      { pathname: '/login', state: { from: { pathname: '/tracker' } } },
    )

    await user.click(screen.getByRole('button', { name: '登录' }))

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith('demo', 'demo123')
    })

    await waitFor(() => {
      expect(screen.getByText('tracker page')).toBeInTheDocument()
    })
  })
})
