import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { interviewApi, resumeApi } from '../lib/api'
import { InterviewPage } from './interview-page'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')

  return {
    ...actual,
    interviewApi: {
      listQuestions: vi.fn(),
      createQuestion: vi.fn(),
      generateQuestions: vi.fn(),
      evaluateAnswer: vi.fn(),
      listSessions: vi.fn(),
      createSession: vi.fn(),
      listRecords: vi.fn(),
      createRecord: vi.fn(),
      evaluateRecord: vi.fn(),
    },
    resumeApi: {
      list: vi.fn(),
    },
  }
})

function renderInterviewPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <InterviewPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('InterviewPage', () => {
  it('imports a local text context and uses it for question generation', async () => {
    const user = userEvent.setup()
    const mockedInterviewApi = vi.mocked(interviewApi)
    const mockedResumeApi = vi.mocked(resumeApi)

    mockedResumeApi.list.mockResolvedValue([])
    mockedInterviewApi.listQuestions.mockResolvedValue([])
    mockedInterviewApi.listSessions.mockResolvedValue([])
    mockedInterviewApi.listRecords.mockResolvedValue([])
    mockedInterviewApi.generateQuestions.mockResolvedValue({
      mode: 'question_generation',
      job_context: 'Remote backend internship with FastAPI and clean architecture.',
      resume_context: null,
      count: 3,
      questions: [],
      raw_content: '',
      provider: null,
      model: null,
    })

    renderInterviewPage()

    expect(screen.getByText('面试准备工作台')).toBeInTheDocument()

    await user.upload(
      screen.getByLabelText(/导入本地上下文/),
      new File(
        ['Remote backend internship with FastAPI and clean architecture.'],
        'job-context.txt',
        { type: 'text/plain' },
      ),
    )

    await waitFor(() =>
      expect(screen.getByDisplayValue('Remote backend internship with FastAPI and clean architecture.')).toBeInTheDocument(),
    )
    expect(screen.getByText(/Imported job-context\.txt/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '生成题目' }))

    await waitFor(() =>
      expect(mockedInterviewApi.generateQuestions).toHaveBeenCalledWith(
        expect.objectContaining({
          job_context: 'Remote backend internship with FastAPI and clean architecture.',
          count: 5,
          resume_id: null,
        }),
      ),
    )
  })
})
