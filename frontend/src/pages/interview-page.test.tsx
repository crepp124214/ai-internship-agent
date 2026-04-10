import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
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
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <InterviewPage />
      </QueryClientProvider>
    </MemoryRouter>,
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

    mockedResumeApi.list.mockResolvedValue([
      { id: 1, title: 'Test Resume', resume_text: 'Test content', processed_content: 'Test content', is_default: true, created_at: '2026-01-01', updated_at: '2026-01-01', user_id: 1, original_file_path: '', file_name: '', file_type: '', file_size: null, language: 'zh-CN' },
    ])
    mockedInterviewApi.listQuestions.mockResolvedValue([])
    mockedInterviewApi.listSessions.mockResolvedValue([])
    mockedInterviewApi.listRecords.mockResolvedValue([])
    mockedInterviewApi.generateQuestions.mockResolvedValue({
      mode: 'question_generation',
      job_context: 'Remote backend internship with FastAPI and clean architecture.',
      resume_context: null,
      count: 3,
      questions: [
        { question_number: 1, question_text: '请介绍一下你使用 FastAPI 的经验', question_type: '技术问题', difficulty: '中等', category: '后端开发' },
        { question_number: 2, question_text: '你是如何设计 RESTful API 的', question_type: '技术问题', difficulty: '中等', category: '后端开发' },
        { question_number: 3, question_text: '请讲解一下异步编程的优势', question_type: '技术问题', difficulty: '中等', category: '后端开发' },
      ],
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
    expect(screen.getByText(/已导入 job-context\.txt/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '生成题目' }))

    await waitFor(() =>
      expect(mockedInterviewApi.generateQuestions).toHaveBeenCalledWith(
        expect.objectContaining({
          job_context: 'Remote backend internship with FastAPI and clean architecture.',
          count: 5,
          resume_id: 1,
        }),
      ),
    )
  })

  it('shows error feedback when generated questions are invalid', async () => {
    const user = userEvent.setup()
    const mockedInterviewApi = vi.mocked(interviewApi)
    const mockedResumeApi = vi.mocked(resumeApi)

    mockedResumeApi.list.mockResolvedValue([
      { id: 1, title: 'Test Resume', resume_text: 'Test content', processed_content: 'Test content', is_default: true, created_at: '2026-01-01', updated_at: '2026-01-01', user_id: 1, original_file_path: '', file_name: '', file_type: '', file_size: null, language: 'zh-CN' },
    ])
    mockedInterviewApi.listQuestions.mockResolvedValue([])
    mockedInterviewApi.listSessions.mockResolvedValue([])
    mockedInterviewApi.listRecords.mockResolvedValue([])
    // Return invalid questions that will be filtered by validateQuestionResponse
    mockedInterviewApi.generateQuestions.mockResolvedValue({
      mode: 'question_generation',
      job_context: 'Test context',
      resume_context: null,
      count: 3,
      questions: [
        { question_number: 1, question_text: 'mock-Test: invalid question', question_type: '技术问题', difficulty: '中等', category: '后端开发' },
      ],
      raw_content: '',
      provider: null,
      model: null,
    })

    renderInterviewPage()

    await user.click(screen.getByRole('button', { name: '生成题目' }))

    await waitFor(() =>
      expect(screen.getByText(/题目生成服务返回了无效内容/)).toBeInTheDocument(),
    )
  })
})
