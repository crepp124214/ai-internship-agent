import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

function renderJobsPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <JobsPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

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

    await user.upload(
      screen.getByLabelText(/Import a local job file/),
      new File(
        ['# Senior Frontend Engineer\nBuild resilient interfaces for candidates.'],
        'Senior-Frontend-Engineer.md',
        { type: 'text/markdown' },
      ),
    )

    await waitFor(() =>
      expect(screen.getByLabelText('Job title')).toHaveValue('Senior Frontend Engineer'),
    )
    expect(screen.getByLabelText('Description')).toHaveValue(
      '# Senior Frontend Engineer\nBuild resilient interfaces for candidates.',
    )
    expect(
      screen.getByText('Imported Senior-Frontend-Engineer.md. The title and description were copied into the form.'),
    ).toBeInTheDocument()

    await user.type(screen.getByLabelText('Company'), 'Acme AI')
    await user.type(screen.getByLabelText('Location'), 'Remote')
    await user.click(screen.getByRole('button', { name: 'Create job' }))

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

    expect(screen.getByText('Job created successfully.')).toBeInTheDocument()
  })
})
