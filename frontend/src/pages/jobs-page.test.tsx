import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { jobsApi, resumeApi } from '../lib/api'
import { JobsPage, validateAiResponse } from './jobs-page'
import { ResultFrame } from './page-primitives'

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
      getRecommendedJobs: vi.fn(),
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
  it('renders jobs page with agent assistant panel', async () => {
    const mockedJobsApi = vi.mocked(jobsApi)
    const mockedResumeApi = vi.mocked(resumeApi)

    mockedJobsApi.list.mockResolvedValue([])
    mockedResumeApi.list.mockResolvedValue([])

    renderJobsPage()

    expect(screen.getByRole('heading', { name: '岗位工作区' })).toBeInTheDocument()
    expect(screen.getByTestId('agent-assistant-panel')).toBeInTheDocument()
  })

  it('shows job list and allows selection', async () => {
    const mockedJobsApi = vi.mocked(jobsApi)
    const mockedResumeApi = vi.mocked(resumeApi)

    mockedJobsApi.list.mockResolvedValue([
      {
        id: 1,
        title: 'Backend Intern',
        company: 'Acme AI',
        location: 'Remote',
        description: 'Build APIs',
        requirements: 'FastAPI',
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
    ])
    mockedResumeApi.list.mockResolvedValue([])

    renderJobsPage()

    // 岗位页收口后，只保留 Agent 助手工作台，不显示独立岗位列表
    // 用户通过 Agent 助手交互获取岗位推荐
    expect(screen.getByTestId('agent-assistant-panel')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Agent 助手' })).toBeInTheDocument()
  })

  describe('validateAiResponse', () => {
    it('should reject content starting with <short assessment>', () => {
      expect(validateAiResponse('<short assessment>|姓名：张三')).toBe(false)
      expect(validateAiResponse('<short assessment>some content')).toBe(false)
    })

    it('should reject content with placeholder fragments like <...>', () => {
      expect(validateAiResponse('Some text <...> more text')).toBe(false)
      expect(validateAiResponse('Test <...> content')).toBe(false)
    })

    it('should reject content with pipe-separated raw resume fragments', () => {
      expect(validateAiResponse('Score 0\n|姓名：张三|学校：xxx|')).toBe(false)
      expect(validateAiResponse('|姓名：张三\n|学校：xxx|')).toBe(false)
    })

    it('should reject prompt injection markers', () => {
      expect(validateAiResponse('mock-generate:Interview Agent')).toBe(false)
      expect(validateAiResponse('prompt: some prompt')).toBe(false)
      expect(validateAiResponse('Task: generate interview questions')).toBe(false)
      expect(validateAiResponse('Agent Prompt Pack')).toBe(false)
    })

    it('should reject too short content', () => {
      expect(validateAiResponse('abc')).toBe(false)
      expect(validateAiResponse('')).toBe(false)
      expect(validateAiResponse(null)).toBe(false)
    })

    it('should accept valid normal content', () => {
      expect(validateAiResponse('Score 85\n\n该简历与岗位匹配度较高')).toBe(true)
      expect(validateAiResponse('该候选人具备扎实的 Python 开发经验，熟悉 FastAPI 框架')).toBe(true)
      expect(validateAiResponse('很好，这个候选人具备出色的能力')).toBe(true)  // 10+ chars
    })
  })

  describe('WorkspaceShell page structure', () => {
    it('renders page shell with title and action area', async () => {
      const mockedJobsApi = vi.mocked(jobsApi)
      const mockedResumeApi = vi.mocked(resumeApi)

      mockedJobsApi.list.mockResolvedValue([])
      mockedResumeApi.list.mockResolvedValue([])

      renderJobsPage()

      // 页面应该使用统一的工作区标题
      expect(screen.getByRole('heading', { name: '岗位工作区' })).toBeInTheDocument()
      // 应该包含动作区
      expect(screen.getByTestId('page-actions')).toBeInTheDocument()
    })
  })

  describe('统一结果区 ResultFrame', () => {
    it('渲染 success 状态下的结果区', () => {
      render(<ResultFrame status="success" title="匹配结果">
        <div>测试内容</div>
      </ResultFrame>)
      expect(screen.getByText(/匹配结果/)).toBeInTheDocument()
      expect(screen.getByText('测试内容')).toBeInTheDocument()
    })

    it('渲染 fallback 状态下的结果区', () => {
      render(<ResultFrame status="fallback" title="岗位匹配结果">
        <div>降级内容</div>
      </ResultFrame>)
      expect(screen.getByText(/当前显示的是降级结果/)).toBeInTheDocument()
    })

    it('渲染 error 状态下的结果区', () => {
      render(<ResultFrame status="error" title="错误">
        <div>错误内容</div>
      </ResultFrame>)
      expect(screen.getByText(/请重试/)).toBeInTheDocument()
    })

    it('渲染 loading 状态下的结果区', () => {
      render(<ResultFrame status="loading" title="加载结果">
        <div data-testid="loading-content">加载中...</div>
      </ResultFrame>)
      expect(screen.getByText(/加载结果/)).toBeInTheDocument()
      expect(screen.getByTestId('loading-content')).toBeInTheDocument()
    })
  })

  describe('岗位页收口 - Agent 主导型布局', () => {
    it('shows agent assistant as only main workbench', () => {
      const mockedJobsApi = vi.mocked(jobsApi)
      const mockedResumeApi = vi.mocked(resumeApi)

      mockedJobsApi.list.mockResolvedValue([
        {
          id: 1,
          title: 'Backend Intern',
          company: 'Acme AI',
          location: 'Remote',
          description: 'Build APIs',
          requirements: 'FastAPI',
          company_logo: null,
          salary: null,
          work_type: null,
          experience: null,
          education: null,
          welfare: null,
          tags: 'Python,FastAPI',
          source: 'manual',
          source_url: null,
          source_id: null,
          is_active: true,
          publish_date: null,
          deadline: null,
          created_at: '2026-04-02T00:00:00Z',
          updated_at: '2026-04-02T00:00:00Z',
        },
      ])
      mockedResumeApi.list.mockResolvedValue([])

      renderJobsPage()

      // 岗位页收口后，只保留唯一的 Agent 助手工作台
      // 独立的 Agent 当前判断区和推荐岗位结果区已删除
      expect(screen.getByTestId('agent-assistant-panel')).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Agent 助手' })).toBeInTheDocument()
      // 不再显示独立的 Agent 当前判断区
      expect(screen.queryByText('Agent 当前判断')).not.toBeInTheDocument()
      // 不再显示独立的推荐岗位结果区
      expect(screen.queryByText('推荐岗位结果')).not.toBeInTheDocument()
    })
  })
})
