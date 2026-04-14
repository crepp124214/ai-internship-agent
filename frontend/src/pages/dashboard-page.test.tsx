import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DashboardPage } from './dashboard-page'

// Use vi.hoisted to create mock functions that can be accessed before initialization
const { mockResumeList, mockJobsList, mockSessionsList, mockQuestionSetsList } = vi.hoisted(() => ({
  mockResumeList: vi.fn().mockResolvedValue([]),
  mockJobsList: vi.fn().mockResolvedValue([]),
  mockSessionsList: vi.fn().mockResolvedValue([]),
  mockQuestionSetsList: vi.fn().mockResolvedValue([]),
}))

// Mock react-router
vi.mock('react-router', () => ({
  useNavigate: () => vi.fn(),
  MemoryRouter: ({ children }: { children: React.ReactNode }) => children,
}))

// Mock API module
vi.mock('../lib/api', () => ({
  resumeApi: {
    list: mockResumeList,
  },
  jobsApi: {
    list: mockJobsList,
  },
  interviewApi: {
    listSessions: mockSessionsList,
    listQuestionSets: mockQuestionSetsList,
  },
}))

// 创建 QueryClient
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

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset default empty values
    mockResumeList.mockResolvedValue([])
    mockJobsList.mockResolvedValue([])
    mockSessionsList.mockResolvedValue([])
    mockQuestionSetsList.mockResolvedValue([])
  })

  function renderDashboardPage(
    resumes: unknown[] = [],
    jobs: unknown[] = [],
    sessions: unknown[] = [],
    questionSets: unknown[] = []
  ) {
    mockResumeList.mockResolvedValue(resumes)
    mockJobsList.mockResolvedValue(jobs)
    mockSessionsList.mockResolvedValue(sessions)
    mockQuestionSetsList.mockResolvedValue(questionSets)

    const queryClient = createTestQueryClient()

    return render(
      <MemoryRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </MemoryRouter>,
    )
  }

  it('renders system overview with title', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '系统总览' })).toBeInTheDocument()
    })
  })

  it('shows single overview panel with summary and latest activity', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText(/暂无数据/)).toBeInTheDocument()
      expect(screen.getByText(/最新活动/)).toBeInTheDocument()
    })
  })

  it('shows three management entry cards', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText('简历管理')).toBeInTheDocument()
      expect(screen.getByText('岗位管理')).toBeInTheDocument()
      expect(screen.getByText('面试管理')).toBeInTheDocument()
    })
  })

  it('dashboard is NOT navigation distribution', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.queryByText('求职 Agent')).not.toBeInTheDocument()
      expect(screen.queryByText('简历优化')).not.toBeInTheDocument()
      expect(screen.queryByText('面试教练')).not.toBeInTheDocument()
      expect(screen.queryByText('快速入口')).not.toBeInTheDocument()
      expect(screen.queryByText('导入数据')).not.toBeInTheDocument()
    })
  })

  describe('真实数据场景', () => {
    it('全部为空时显示兜底总结', async () => {
      renderDashboardPage([], [], [], [])

      await waitFor(() => {
        expect(screen.getByText(/暂无数据/)).toBeInTheDocument()
      })
      expect(screen.getByText(/暂无活动记录/)).toBeInTheDocument()
    })

    it('有简历、无岗位时显示对应总结', async () => {
      const resumes = [
        { id: 1, title: '测试简历', is_default: true, created_at: '2026-04-01' },
      ]
      renderDashboardPage(resumes, [], [], [])

      await waitFor(() => {
        expect(screen.getByText(/你已经完成简历准备/)).toBeInTheDocument()
      })
    })

    it('有岗位、无题集时显示对应总结', async () => {
      const jobs = [
        { id: 1, title: '后端开发', is_active: true, created_at: '2026-04-01' },
      ]
      renderDashboardPage([], jobs, [], [])

      await waitFor(() => {
        expect(screen.getByText(/你已经进入岗位筛选阶段/)).toBeInTheDocument()
      })
    })

    it('有题集时"最新活动"优先显示题集', async () => {
      const questionSets = [
        { id: 1, title: '后端开发题集', created_at: '2026-04-11T10:00:00Z' },
      ]
      renderDashboardPage([], [], [], questionSets)

      await waitFor(() => {
        expect(screen.getByText(/保存了"后端开发题集"/)).toBeInTheDocument()
      })
    })

    it('有完成面试时总结文案切换', async () => {
      // 注意：题集优先级高于完成面试，所以这里不传 questionSets
      const sessions = [
        {
          id: 1,
          completed: 1,
          created_at: '2026-04-11T10:00:00Z',
        },
      ]
      renderDashboardPage([], [], sessions, [])

      await waitFor(() => {
        expect(screen.getByText(/你最近完成了一轮面试练习/)).toBeInTheDocument()
      })
    })

    it('管理入口卡显示真实数量', async () => {
      const resumes = [
        { id: 1, title: '简历1', is_default: true, created_at: '2026-04-01' },
        { id: 2, title: '简历2', is_default: false, created_at: '2026-04-01' },
      ]
      const jobs = [
        { id: 1, title: '岗位1', is_active: true, created_at: '2026-04-01' },
        { id: 2, title: '岗位2', is_active: true, created_at: '2026-04-01' },
        { id: 3, title: '岗位3', is_active: false, created_at: '2026-04-01' },
      ]
      const sessions = [
        { id: 1, completed: 1, created_at: '2026-04-01' },
        { id: 2, completed: 0, created_at: '2026-04-01' },
      ]
      const questionSets = [
        { id: 1, title: '题集1', created_at: '2026-04-01' },
      ]

      renderDashboardPage(resumes, jobs, sessions, questionSets)

      await waitFor(() => {
        // 简历管理：2份简历，1份默认
        expect(screen.getByText(/2 份简历.*1 份默认/)).toBeInTheDocument()
        // 岗位管理：3个目标，2个进行中
        expect(screen.getByText(/3 个目标.*2 个进行中/)).toBeInTheDocument()
        // 面试管理：2次练习，1个题集
        expect(screen.getByText(/2 次练习.*1 个题集/)).toBeInTheDocument()
      })
    })

    it('局部接口失败时页面仍能渲染', async () => {
      mockResumeList.mockRejectedValue(new Error('Network error'))

      const queryClient = createTestQueryClient()

      // 这不应该抛出错误，页面应该能渲染
      expect(() => {
        render(
          <MemoryRouter>
            <QueryClientProvider client={queryClient}>
              <DashboardPage />
            </QueryClientProvider>
          </MemoryRouter>,
        )
      }).not.toThrow()

      // 兜底数据应该显示
      await waitFor(() => {
        expect(screen.getByText(/暂无数据/)).toBeInTheDocument()
      })
    })

    it('最新活动优先级：题集 > 完成面试 > 岗位 > 简历', async () => {
      const resumes = [{ id: 1, title: '简历1', created_at: '2026-04-05' }]
      const jobs = [{ id: 1, title: '岗位1', created_at: '2026-04-08' }]
      const sessions = [
        { id: 1, completed: 1, created_at: '2026-04-10' },
      ]
      const questionSets = [
        { id: 1, title: '题集1', created_at: '2026-04-11' },
      ]

      // 题集最新，应该显示题集
      renderDashboardPage(resumes, jobs, sessions, questionSets)

      await waitFor(() => {
        expect(screen.getByText(/保存了"题集1"/)).toBeInTheDocument()
      })
    })
  })
})