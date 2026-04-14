import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AgentConfigPage } from './agent-config-page'

const { mockGetUserLlmConfigs } = vi.hoisted(() => ({
  mockGetUserLlmConfigs: vi.fn(),
}))

vi.mock('../../lib/api', () => ({
  getUserLlmConfigs: mockGetUserLlmConfigs,
  saveUserLlmConfig: vi.fn(),
  deleteUserLlmConfig: vi.fn(),
  testGlobalLlmConfig: vi.fn(),
  testAgentLlmConfig: vi.fn(),
}))

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })
}

function createDeferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    void rej
  })

  return { promise, resolve }
}

describe('AgentConfigPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows syncing state while configs are loading and then reflects the loaded count', async () => {
    const deferred = createDeferred<
      Array<{ agent: string; provider: string; model: string; api_key: string | null; base_url: string | null; temperature: number; is_active: boolean; updated_at: string }>
    >()
    mockGetUserLlmConfigs.mockImplementation(() => deferred.promise)

    const queryClient = createTestQueryClient()

    render(
      <MemoryRouter>
        <QueryClientProvider client={queryClient}>
          <AgentConfigPage />
        </QueryClientProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText('同步配置中...')).toBeInTheDocument()
    expect(screen.queryByText(/0 \/ 3 个 Agent/)).not.toBeInTheDocument()

    deferred.resolve([
      {
        agent: 'resume_agent',
        provider: 'openai',
        model: 'gpt-4o-mini',
        api_key: 'key-1',
        base_url: null,
        temperature: 0.7,
        is_active: true,
        updated_at: '2026-04-12T00:00:00Z',
      },
      {
        agent: 'job_agent',
        provider: 'openai',
        model: 'gpt-4o-mini',
        api_key: 'key-2',
        base_url: null,
        temperature: 0.7,
        is_active: true,
        updated_at: '2026-04-12T00:00:00Z',
      },
      {
        agent: 'interview_agent',
        provider: 'openai',
        model: 'gpt-4o-mini',
        api_key: 'key-3',
        base_url: null,
        temperature: 0.7,
        is_active: true,
        updated_at: '2026-04-12T00:00:00Z',
      },
    ])

    await waitFor(() => {
      expect(screen.getByText(/3 \/ 3 个 Agent/)).toBeInTheDocument()
    })
  })
})
