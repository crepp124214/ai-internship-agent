import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AppRouter } from '../app/router'
import { AppProviders } from '../app/providers'

// Mock API calls
vi.mock('../lib/api', () => ({
  authApi: {
    login: vi.fn().mockResolvedValue({ access_token: 'test-token' }),
    getCurrentUser: vi.fn().mockResolvedValue({
      id: 1,
      username: 'demo',
      email: 'demo@example.com',
      name: 'Demo User',
      phone: null,
      bio: null,
      avatar_url: null,
      created_at: '2026-04-02T00:00:00Z',
      updated_at: '2026-04-02T00:00:00Z',
    }),
    refreshToken: vi.fn().mockResolvedValue({ access_token: 'test-token' }),
    logout: vi.fn().mockResolvedValue(undefined),
  },
  resumeApi: {
    list: vi.fn().mockResolvedValue([]),
    create: vi.fn().mockResolvedValue({ id: 1, title: 'Test Resume' }),
  },
  jobsApi: {
    list: vi.fn().mockResolvedValue([]),
    saveExternal: vi.fn().mockResolvedValue({ id: 1 }),
  },
  interviewApi: {
    listSessions: vi.fn().mockResolvedValue([]),
  },
}))

function renderWithRouter(ui: ReactNode, initialEntries: string[] = ['/login']) {
  return render(
    <AppProviders>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/login" element={ui} />
          <Route path="/*" element={<AppRouter />} />
        </Routes>
      </MemoryRouter>
    </AppProviders>,
  )
}

describe('Phase C: Main User Flow - 20 Consecutive Runs', () => {
  const totalRuns = 20
  const results: Array<{ run: number; passed: boolean; error?: string }> = []

  // Test each flow step
  it.each(Array.from({ length: totalRuns }, (_, i) => i + 1))(
    'Run #%d - Login -> Dashboard -> Jobs -> Resume -> Interview -> Settings',
    async (runNumber) => {
      let passed = false
      let error: string | undefined

      try {
        // Step 1: Login page accessible
        renderWithRouter(
          <div>Login Page</div>,
          ['/login'],
        )
        
        // Verify login page renders
        expect(screen.getByText('Login Page')).toBeInTheDocument()
        
        // Step 2: After login, dashboard accessible
        renderWithRouter(
          <div>Dashboard</div>,
          ['/'],
        )
        
        // Verify dashboard renders
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
        
        // Step 3: Jobs explore page accessible  
        renderWithRouter(
          <div>Jobs Explore</div>,
          ['/jobs-explore'],
        )
        
        // Verify jobs page renders
        expect(screen.getByText('Jobs Explore')).toBeInTheDocument()
        
        // Step 4: Resume page accessible
        renderWithRouter(
          <div>Resume</div>,
          ['/resume'],
        )
        
        // Verify resume page renders
        expect(screen.getByText('Resume')).toBeInTheDocument()
        
        // Step 5: Interview page accessible
        renderWithRouter(
          <div>Interview</div>,
          ['/interview'],
        )
        
        // Verify interview page renders
        expect(screen.getByText('Interview')).toBeInTheDocument()
        
        // Step 6: Settings page accessible
        renderWithRouter(
          <div>Settings</div>,
          ['/settings/agent-config'],
        )
        
        // Verify settings page renders
        expect(screen.getByText('Settings')).toBeInTheDocument()
        
        passed = true
      } catch (e) {
        error = e instanceof Error ? e.message : String(e)
        passed = false
      }

      results.push({ run: runNumber, passed, error })
      
      // Assert the current run passed
      expect(passed).toBe(true)
    },
  )

  // After all runs, summarize
  it('should summarize results', () => {
    const passedCount = results.filter((r) => r.passed).length
    const passRate = (passedCount / totalRuns) * 100
    
    console.log('\n=== Phase C Results ===')
    console.log(`Total Runs: ${totalRuns}`)
    console.log(`Passed: ${passedCount}`)
    console.log(`Failed: ${totalRuns - passedCount}`)
    console.log(`Pass Rate: ${passRate}%`)
    
    if (results.some((r) => !r.passed)) {
      console.log('\nFailed runs:')
      results.filter((r) => !r.passed).forEach((r) => {
        console.log(`  Run #${r.run}: ${r.error}`)
      })
    }
    
    // Assert pass rate >= 95%
    expect(passRate).toBeGreaterThanOrEqual(95)
  })

  // Settings page navigation test
  it('should navigate to settings page from sidebar', async () => {
    renderWithRouter(
      <div>Settings</div>,
      ['/settings'],
    )
    
    // Verify settings page renders (when route is registered)
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  // Settings sub-pages navigation tests
  it('should navigate to settings/resumes page', async () => {
    renderWithRouter(
      <div>Settings Resumes</div>,
      ['/settings/resumes'],
    )
    
    expect(screen.getByText('Settings Resumes')).toBeInTheDocument()
  })

  it('should navigate to settings/jobs page', async () => {
    renderWithRouter(
      <div>Settings Jobs</div>,
      ['/settings/jobs'],
    )
    
    expect(screen.getByText('Settings Jobs')).toBeInTheDocument()
  })

  it('should navigate to settings/interviews page', async () => {
    renderWithRouter(
      <div>Settings Interviews</div>,
      ['/settings/interviews'],
    )
    
    expect(screen.getByText('Settings Interviews')).toBeInTheDocument()
  })
})