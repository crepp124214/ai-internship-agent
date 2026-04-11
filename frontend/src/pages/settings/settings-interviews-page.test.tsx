import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SettingsInterviewsPage } from './settings-interviews-page'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router', async () => {
  const actual = await vi.importActual('react-router')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../../lib/api', () => ({
  interviewApi: {
    listSessions: vi.fn().mockResolvedValue([
      {
        id: 1,
        user_id: 1,
        job_id: null,
        session_type: 'technical',
        duration: 25,
        total_questions: 8,
        average_score: 78,
        completed: 1,
        created_at: '2026-01-15T10:00:00',
        updated_at: '2026-01-15T10:25:00',
      },
      {
        id: 2,
        user_id: 1,
        job_id: null,
        session_type: 'behavior',
        duration: null,
        total_questions: 5,
        average_score: null,
        completed: 0,
        created_at: '2026-01-16T14:00:00',
        updated_at: '2026-01-16T14:00:00',
      },
    ]),
    listQuestionSets: vi.fn().mockResolvedValue([
      {
        id: 1,
        user_id: 1,
        title: '前端面试题集',
        job_id: null,
        resume_id: null,
        source: 'generated',
        status: 'active',
        questions: [
          { question_number: 1, question_text: '什么是 React Hooks?', question_type: 'technical', difficulty: 'medium', category: '前端' },
          { question_number: 2, question_text: '解释 virtual DOM', question_type: 'technical', difficulty: 'easy', category: '前端' },
        ],
        created_at: '2026-01-10T00:00:00',
        updated_at: '2026-01-10T00:00:00',
      },
    ]),
    coachGetReport: vi.fn().mockResolvedValue({
      session_id: 1,
      review_report: {
        dimensions: [],
        overall_score: 78,
        overall_comment: '表现良好',
        improvement_suggestions: ['可以加强算法'],
        markdown: '# report',
      },
      average_score: 78,
    }),
    startCoachFromQuestionSet: vi.fn().mockResolvedValue({}),
  },
  readApiError: vi.fn().mockReturnValue('请求失败'),
}))

function renderSettingsInterviewsPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <MemoryRouter initialEntries={['/settings/interviews']}>
      <QueryClientProvider client={queryClient}>
        <Routes>
          <Route path="/settings/interviews" element={<SettingsInterviewsPage />} />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SettingsInterviewsPage', () => {
  it('renders interview management page with report view', async () => {
    renderSettingsInterviewsPage()

    expect(screen.getByText('面试记录')).toBeInTheDocument()
    expect(screen.getByText('查看历史练习和 AI 评估报告')).toBeInTheDocument()

    // Wait for data to load
    await screen.findByText('技术面试')
  })

  it('shows question set reuse entry', async () => {
    renderSettingsInterviewsPage()

    // Wait for data
    await screen.findByText('技术面试')

    // Should show question set reuse section
    expect(screen.getByText(/题集复用/)).toBeInTheDocument()
  })

  it('shows 从题集开始练习 button when question sets exist', async () => {
    renderSettingsInterviewsPage()

    // Wait for data
    await screen.findByText('技术面试')

    // Should have start practice button
    expect(screen.getByText('从题集开始练习')).toBeInTheDocument()
  })

  it('displays session list with score and status', async () => {
    renderSettingsInterviewsPage()

    await screen.findByText('技术面试')

    // Should show scores
    expect(screen.getByText('78')).toBeInTheDocument()

    // Should show status
    expect(screen.getByText('已完成')).toBeInTheDocument()
    expect(screen.getByText('进行中')).toBeInTheDocument()
  })
})