import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { interviewApi, jobsApi, resumeApi } from '../lib/api'
import { InterviewPage } from './interview-page'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')

  return {
    ...actual,
    interviewApi: {
      listQuestions: vi.fn(),
      createQuestion: vi.fn(),
      listQuestionSets: vi.fn(),
      createQuestionSet: vi.fn(),
      startCoachFromQuestionSet: vi.fn(),
      generateQuestions: vi.fn(),
      evaluateAnswer: vi.fn(),
      listSessions: vi.fn(),
      createSession: vi.fn(),
      listRecords: vi.fn(),
      createRecord: vi.fn(),
      evaluateRecord: vi.fn(),
      coachStart: vi.fn(),
      coachAnswer: vi.fn(),
      coachFollowup: vi.fn(),
      coachEnd: vi.fn(),
      coachGetReport: vi.fn(),
    },
    resumeApi: {
      list: vi.fn(),
    },
    jobsApi: {
      list: vi.fn(),
    },
  }
})

function renderInterviewPage(initialEntries: Array<string | { pathname: string; state?: unknown }> = ['/interview']) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={queryClient}>
        <InterviewPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

function mockDefaultInterviewData() {
  vi.mocked(resumeApi).list.mockResolvedValue([
    {
      id: 1,
      title: 'Test Resume',
      resume_text: 'Test content',
      processed_content: 'Test content',
      is_default: true,
      created_at: '2026-01-01',
      updated_at: '2026-01-01',
      user_id: 1,
      original_file_path: '',
      file_name: '',
      file_type: '',
      file_size: null,
      language: 'zh-CN',
    },
  ])
  vi.mocked(jobsApi).list.mockResolvedValue([
    {
      id: 2,
      title: 'Backend Intern',
      company: 'Acme',
      location: 'Beijing',
      description: 'Build APIs',
      requirements: null,
      company_logo: null,
      salary: null,
      work_type: 'internship',
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
      created_at: '2026-01-01',
      updated_at: '2026-01-01',
    },
  ])
  vi.mocked(interviewApi).listQuestions.mockResolvedValue([])
  vi.mocked(interviewApi).listQuestionSets.mockResolvedValue([])
  vi.mocked(interviewApi).listSessions.mockResolvedValue([])
  vi.mocked(interviewApi).listRecords.mockResolvedValue([])
  vi.mocked(interviewApi).coachGetReport.mockResolvedValue({
    session_id: 1,
    review_report: {
      dimensions: [],
      overall_score: 79,
      overall_comment: '最近一次表现稳定',
      improvement_suggestions: [],
      markdown: '',
    },
    average_score: 79,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockDefaultInterviewData()
})

describe('InterviewPage', () => {
  it('renders workbench layout correctly', async () => {
    vi.mocked(resumeApi).list.mockResolvedValue([])
    vi.mocked(jobsApi).list.mockResolvedValue([])
    vi.mocked(interviewApi).listQuestionSets.mockResolvedValue([])

    renderInterviewPage()

    expect(screen.getByText('面试工作区')).toBeInTheDocument()
    // First row
    expect(screen.getByText('当前题集')).toBeInTheDocument()
    expect(screen.getByText('面试教练')).toBeInTheDocument()
    // Second row
    expect(screen.getByText('最近训练结果')).toBeInTheDocument()
    expect(screen.getByText('历史题集')).toBeInTheDocument()
    expect(screen.getAllByTestId('result-frame')).toHaveLength(2)
  })

  it('shows start practice button', async () => {
    vi.mocked(resumeApi).list.mockResolvedValue([])
    vi.mocked(jobsApi).list.mockResolvedValue([])
    vi.mocked(interviewApi).listQuestionSets.mockResolvedValue([])

    renderInterviewPage()

    expect(screen.getByRole('button', { name: '开始练习' })).toBeInTheDocument()
  })
})

describe('面试页收口 - 训练工作台型布局', () => {
    it('shows workbench layout with current question set and coach entry', async () => {
      vi.mocked(resumeApi).list.mockResolvedValue([])
      vi.mocked(jobsApi).list.mockResolvedValue([])
      vi.mocked(interviewApi).listQuestionSets.mockResolvedValue([])
      vi.mocked(interviewApi).generateQuestions.mockResolvedValue({
        mode: 'question_generation',
        job_context: '',
        resume_context: null,
        count: 0,
        questions: [],
        raw_content: '',
        provider: 'mock',
        model: null,
        status: 'success',
      })

      renderInterviewPage()

      // First row: current question set + coach entry
      expect(screen.getByText('当前题集')).toBeInTheDocument()
      expect(screen.getByText('面试教练')).toBeInTheDocument()
      // Second row: training result summary + history
      expect(screen.getByText('最近训练结果')).toBeInTheDocument()
      expect(screen.getByText('历史题集')).toBeInTheDocument()
})
})

describe('InterviewPage score rendering', () => {
  it('uses backend score when immediate feedback is a placeholder', async () => {
    const user = userEvent.setup()

    vi.mocked(interviewApi).coachStart.mockResolvedValue({
      session_id: 99,
      opening_message: '开始训练',
      first_question: '请做一个自我介绍',
    })
    vi.mocked(interviewApi).coachAnswer.mockResolvedValue({
      score: 88,
      feedback: '评分暂不可用',
      next_question: null,
    })

    renderInterviewPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '开始练习' })).toBeEnabled()
    })

    await user.click(screen.getByRole('button', { name: '开始练习' }))

    await waitFor(() => {
      expect(screen.getByText('面试练习中')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('输入你的回答...'), { target: { value: '这是我的回答' } })
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '提交回答' })).toBeEnabled()
    })
    await user.click(screen.getByRole('button', { name: '提交回答' }))

    await waitFor(() => {
      expect(screen.getAllByText(/本题得分：88分/).length).toBeGreaterThan(0)
      expect(screen.queryByText('评分暂不可用')).not.toBeInTheDocument()
    })
  })

  it('loads latest completed session report into recent result card', async () => {
    vi.mocked(interviewApi).listQuestionSets.mockResolvedValue([])
    vi.mocked(interviewApi).listSessions.mockResolvedValue([
      {
        id: 101,
        user_id: 1,
        job_id: 2,
        session_type: 'technical',
        duration: 18,
        total_questions: 3,
        average_score: 79,
        completed: 1,
        created_at: '2026-04-12T09:00:00',
        updated_at: '2026-04-12T09:30:00',
      },
    ])
    vi.mocked(interviewApi).coachGetReport.mockResolvedValue({
      session_id: 101,
      review_report: {
        dimensions: [],
        overall_score: 79,
        overall_comment: '最近一次表现稳定',
        improvement_suggestions: [],
        markdown: '',
      },
      average_score: 79,
    })

    renderInterviewPage()

    expect(await screen.findByText('平均 79 分')).toBeInTheDocument()
    expect(screen.getByText('最近一次表现稳定')).toBeInTheDocument()
    expect(screen.getByText('18 分钟')).toBeInTheDocument()
  })

  it('selects question set from navigation state and shows its title', async () => {
    vi.mocked(interviewApi).listQuestionSets.mockResolvedValue([
      {
        id: 11,
        user_id: 1,
        title: '默认题集',
        job_id: null,
        resume_id: null,
        source: 'generated',
        status: 'active',
        questions: [
          { question_number: 1, question_text: '默认问题', question_type: 'technical', difficulty: 'easy', category: '通用' },
        ],
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      {
        id: 22,
        user_id: 1,
        title: '目标题集',
        job_id: null,
        resume_id: null,
        source: 'generated',
        status: 'active',
        questions: [
          { question_number: 1, question_text: '目标问题一', question_type: 'technical', difficulty: 'medium', category: '后端' },
          { question_number: 2, question_text: '目标问题二', question_type: 'technical', difficulty: 'medium', category: '后端' },
        ],
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
    ])

    renderInterviewPage([{ pathname: '/interview', state: { questionSetId: 22 } }])

    expect((await screen.findAllByText('目标题集')).length).toBeGreaterThan(0)
    expect(screen.getByText(/目标问题一/)).toBeInTheDocument()
  })
})
