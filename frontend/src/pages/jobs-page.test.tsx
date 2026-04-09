import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { jobsApi, resumeApi, type Job } from '../lib/api'
import { JobsPage } from './jobs-page'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')

  return {
    ...actual,
    jobsApi: {
      list: vi.fn(),
      create: vi.fn(),
      previewMatch: vi.fn(),
      persistMatch: vi.fn(),
      getMatchHistory: vi.fn(),
      saveExternal: vi.fn(),
    },
    resumeApi: {
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      previewSummary: vi.fn(),
      persistSummary: vi.fn(),
      getSummaryHistory: vi.fn(),
      previewImprovements: vi.fn(),
      persistImprovements: vi.fn(),
      getOptimizationHistory: vi.fn(),
    },
  }
})

// Mock scrollIntoView for JSDOM
beforeEach(() => {
  vi.clearAllMocks()
  if (typeof window !== 'undefined') {
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
  }
})

function renderJobsPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <JobsPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('JobsPage', () => {
  it('imports a local markdown job file, fills the form, and creates the job', async () => {
    const user = userEvent.setup()
    const mockedJobsApi = vi.mocked(jobsApi)
    const mockedResumeApi = vi.mocked(resumeApi)
    let jobs: Job[] = []

    mockedJobsApi.list.mockImplementation(async () => jobs)
    mockedJobsApi.getMatchHistory.mockResolvedValue([])
    mockedResumeApi.list.mockResolvedValue([])
    mockedJobsApi.create.mockImplementation(async (payload) => {
      const createdJob: Job = {
        id: 101,
        title: payload.title,
        company: payload.company,
        location: payload.location,
        description: payload.description,
        requirements: payload.requirements ?? null,
        company_logo: null,
        salary: null,
        work_type: null,
        experience: null,
        education: null,
        welfare: null,
        tags: null,
        source: payload.source,
        source_url: null,
        source_id: null,
        is_active: true,
        publish_date: null,
        deadline: null,
        created_at: '2026-04-02T00:00:00Z',
        updated_at: '2026-04-02T00:00:00Z',
      }

      jobs = [createdJob]
      return createdJob
    })

    renderJobsPage()

    expect(screen.getByText('探索公司岗位并分析匹配')).toBeInTheDocument()

    await user.upload(
      screen.getByLabelText(/导入本地岗位文件/),
      new File(
        ['# Senior Frontend Engineer\nBuild resilient interfaces for candidates.'],
        'Senior-Frontend-Engineer.md',
        { type: 'text/markdown' },
      ),
    )

    await waitFor(() =>
      expect(screen.getByLabelText('岗位标题')).toHaveValue('Senior Frontend Engineer'),
    )
    expect(screen.getByLabelText('岗位描述')).toHaveValue(
      '# Senior Frontend Engineer\nBuild resilient interfaces for candidates.',
    )
    expect(
      screen.getByText('已导入 Senior-Frontend-Engineer.md，岗位标题和描述已填入表单。'),
    ).toBeInTheDocument()

    await user.type(screen.getByLabelText('公司'), 'Acme AI')
    await user.type(screen.getByLabelText('地点'), 'Remote')
    await user.click(screen.getByRole('button', { name: '创建岗位' }))

    await waitFor(() => expect(mockedJobsApi.create).toHaveBeenCalled())
    expect(mockedJobsApi.create.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({
        title: 'Senior Frontend Engineer',
        company: 'Acme AI',
        location: 'Remote',
        description: '# Senior Frontend Engineer\nBuild resilient interfaces for candidates.',
        source: 'local_file',
      }),
    )

    expect(screen.getByText('岗位创建成功。')).toBeInTheDocument()
  })
})