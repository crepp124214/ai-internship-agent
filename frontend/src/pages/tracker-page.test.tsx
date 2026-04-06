import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { jobsApi, resumeApi, trackerApi, type ApplicationTracker, type Job, type Resume } from '../lib/api'
import { TrackerPage } from './tracker-page'

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
    trackerApi: {
      listApplications: vi.fn(),
      createApplication: vi.fn(),
      previewAdvice: vi.fn(),
      persistAdvice: vi.fn(),
      getAdviceHistory: vi.fn(),
    },
  }
})

function renderTrackerPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <TrackerPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('TrackerPage', () => {
  it('imports a local JSON tracker note, fills the form, and creates the application', async () => {
    const user = userEvent.setup()
    const mockedJobsApi = vi.mocked(jobsApi)
    const mockedResumeApi = vi.mocked(resumeApi)
    const mockedTrackerApi = vi.mocked(trackerApi)

    const jobs: Job[] = [
      {
        id: 7,
        title: 'Frontend Intern',
        company: 'Acme AI',
        location: 'Remote',
        description: 'Build candidate-facing UI',
        requirements: null,
        company_logo: null,
        salary: null,
        work_type: null,
        experience: null,
        education: null,
        welfare: null,
        tags: null,
        source: 'manual',
        source_url: null,
        source_id: null,
        is_active: true,
        publish_date: null,
        deadline: null,
        created_at: '2026-04-02T00:00:00Z',
        updated_at: '2026-04-02T00:00:00Z',
      },
    ]
    const resumes: Resume[] = [
      {
        id: 4,
        user_id: 1,
        title: 'Portfolio Resume',
        original_file_path: 'uploads/4-resume.md',
        file_name: 'resume.md',
        file_type: 'text/markdown',
        file_size: 128,
        processed_content: null,
        resume_text: null,
        language: 'en',
        is_default: false,
        created_at: '2026-04-02T00:00:00Z',
        updated_at: '2026-04-02T00:00:00Z',
      },
    ]
    let applications: ApplicationTracker[] = []

    mockedJobsApi.list.mockResolvedValue(jobs)
    mockedResumeApi.list.mockResolvedValue(resumes)
    mockedTrackerApi.listApplications.mockImplementation(async () => applications)
    mockedTrackerApi.getAdviceHistory.mockResolvedValue([])
    mockedTrackerApi.createApplication.mockImplementation(async (payload) => {
      const createdApplication: ApplicationTracker = {
        id: 88,
        user_id: 1,
        job_id: payload.job_id,
        resume_id: payload.resume_id,
        status: payload.status,
        notes: payload.notes ?? null,
        application_date: '2026-04-02T00:00:00Z',
        status_updated_at: '2026-04-02T00:00:00Z',
        created_at: '2026-04-02T00:00:00Z',
        updated_at: '2026-04-02T00:00:00Z',
      }

      applications = [createdApplication]
      return createdApplication
    })

    renderTrackerPage()

    expect(screen.getByText('投递追踪工作台')).toBeInTheDocument()

    await user.upload(
      screen.getByLabelText(/本地备注文件/),
      new File(
        [
          JSON.stringify({
            job_id: 7,
            resume_id: 4,
            status: 'screening',
            notes: 'Waiting for recruiter follow-up after the application review.',
          }),
        ],
        'tracker-note.json',
        { type: 'application/json' },
      ),
    )

    await waitFor(() => expect(screen.getByLabelText('岗位')).toHaveValue('7'))
    expect(screen.getByLabelText('简历')).toHaveValue('4')
    expect(screen.getByLabelText('当前状态')).toHaveValue('screening')
    expect(screen.getByLabelText('备注')).toHaveValue('Waiting for recruiter follow-up after the application review.')
    expect(screen.getByText('Imported tracker-note.json. The tracker form was updated.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '创建投递记录' }))

    await waitFor(() =>
      expect(mockedTrackerApi.createApplication).toHaveBeenCalledWith(
        expect.objectContaining({
          job_id: 7,
          resume_id: 4,
          status: 'screening',
          notes: 'Waiting for recruiter follow-up after the application review.',
        }),
      ),
    )

    expect(screen.getByText('Application record created. You can now preview or save AI guidance.')).toBeInTheDocument()
  })
})
