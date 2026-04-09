import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AuthenticatedAppShell } from '../layout/authenticated-app-shell'
import { AuthContext, type AuthContextValue } from '../auth/use-auth'
import { LoginPage } from './login-page'

function renderWithAuth(ui: ReactNode, value: AuthContextValue, initialEntries: string[] = ['/login']) {
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </AuthContext.Provider>,
  )
}

const loggedOutContext: AuthContextValue = {
  token: null,
  user: null,
  isBootstrapping: false,
  isAuthenticated: false,
  login: async () => undefined,
  logout: async () => undefined,
  refreshCurrentUser: async () => undefined,
  refreshToken: async () => undefined,
}

const loggedInContext: AuthContextValue = {
  token: 'token-123',
  user: {
    id: 1,
    username: 'demo',
    email: 'demo@example.com',
    name: 'Demo User',
    phone: null,
    bio: null,
    avatar_url: null,
    created_at: '2026-04-02T00:00:00Z',
    updated_at: '2026-04-02T00:00:00Z',
  },
  isBootstrapping: false,
  isAuthenticated: true,
  login: async () => undefined,
  logout: async () => undefined,
  refreshCurrentUser: async () => undefined,
  refreshToken: async () => undefined,
}

describe('Wave 5 frontend smoke', () => {
  it('renders the productized login copy', () => {
    renderWithAuth(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>,
      loggedOutContext,
    )

    expect(screen.getByText('AI 实习求职工作台')).toBeInTheDocument()
    expect(screen.getByText('开始你的下一段求职推进')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument()
  })

  it('renders the authenticated shell with core navigation labels', () => {
    renderWithAuth(
      <Routes>
        <Route element={<AuthenticatedAppShell />}>
          <Route path="/dashboard" element={<div>dashboard content</div>} />
        </Route>
      </Routes>,
      loggedInContext,
      ['/dashboard'],
    )

    expect(screen.getByText('AI 求职工作台')).toBeInTheDocument()
    expect(screen.getAllByText('仪表盘').length).toBeGreaterThan(0)
    expect(screen.getByText('简历优化')).toBeInTheDocument()
    expect(screen.getByText('面试准备')).toBeInTheDocument()
    expect(screen.getByText('设置中心')).toBeInTheDocument()
  })
})
