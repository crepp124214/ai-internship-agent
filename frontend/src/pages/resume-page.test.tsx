import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { jobsApi, resumeApi } from '../lib/api'
import { ResumePage } from './resume-page'
import { ResultFrame } from './page-primitives'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')

  return {
    ...actual,
    resumeApi: {
      list: vi.fn(),
      previewSummary: vi.fn(),
      persistSummary: vi.fn(),
      getSummaryHistory: vi.fn(),
      previewImprovements: vi.fn(),
      persistImprovements: vi.fn(),
      getOptimizationHistory: vi.fn(),
      customizeForJd: vi.fn(),
    },
    jobsApi: {
      list: vi.fn(),
    },
  }
})

function renderResumePage() {
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
        <ResumePage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

const MOCK_RESUME = {
  id: 1,
  user_id: 1,
  title: 'Test Resume',
  original_file_path: '',
  file_name: 'test.md',
  file_type: 'text/markdown',
  file_size: null,
  processed_content: 'Test resume content',
  resume_text: 'Test resume content',
  language: 'en',
  is_default: false,
  created_at: '2026-04-02T00:00:00Z',
  updated_at: '2026-04-02T00:00:00Z',
}

const MOCK_JOB = {
  id: 1,
  title: 'Backend Engineer',
  company: 'ByteDance',
  company_logo: null,
  description: 'Backend work',
  requirements: 'Python',
  location: 'Beijing',
  salary: '30k-50k',
  work_type: null,
  experience: null,
  education: null,
  welfare: null,
  tags: null,
  source: 'import',
  source_url: null,
  source_id: null,
  is_active: true,
  publish_date: null,
  deadline: null,
  created_at: '2026-04-01T00:00:00Z',
  updated_at: '2026-04-01T00:00:00Z',
}

describe('ResumePage', () => {
  it('no longer renders create resume entry', async () => {
    vi.mocked(resumeApi.list).mockResolvedValue([])
    vi.mocked(jobsApi.list).mockResolvedValue([])

    renderResumePage()

    expect(screen.queryByText('创建 / 导入简历')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('新建简历')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '创建' })).not.toBeInTheDocument()
  })

  it('no longer renders import resume entry', async () => {
    vi.mocked(resumeApi.list).mockResolvedValue([])
    vi.mocked(jobsApi.list).mockResolvedValue([])

    renderResumePage()

    expect(screen.queryByLabelText(/导入本地简历/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '导入并创建' })).not.toBeInTheDocument()
  })

  it('renders target job section and optimization buttons when resumes exist', async () => {
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])

    renderResumePage()

    await waitFor(() => {
      expect(screen.getByText('当前简历')).toBeInTheDocument()
    })
    expect(screen.getByText('结果总览')).toBeInTheDocument()
    expect(screen.getByText('操作')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'JD 定向优化' })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '预览摘要' })).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: '预览优化建议' })).toBeInTheDocument()
  })

  it('shows workbench layout when no resumes', async () => {
    vi.mocked(resumeApi.list).mockResolvedValue([])
    vi.mocked(jobsApi.list).mockResolvedValue([])

    renderResumePage()

    await waitFor(() => {
      expect(screen.getByText('当前简历')).toBeInTheDocument()
    })
    expect(screen.getByText('结果总览')).toBeInTheDocument()
    expect(screen.getByText('操作')).toBeInTheDocument()
  })

  it('calls previewSummary when 预览摘要 is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])
    vi.mocked(resumeApi.previewSummary).mockResolvedValue({
      mode: 'summary',
      resume_id: 1,
      target_role: null,
      content: 'Summary content',
      raw_content: 'Test resume content',
      provider: 'mock',
      model: 'mock-model',
      status: 'success',
      fallback_used: false,
    })

    renderResumePage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '预览摘要' })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: '预览摘要' }))

    await waitFor(() => {
      expect(resumeApi.previewSummary).toHaveBeenCalledWith(1, { target_role: null })
    })
  })

  it('calls previewImprovements when 预览优化建议 is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])
    vi.mocked(resumeApi.previewImprovements).mockResolvedValue({
      mode: 'improvements',
      resume_id: 1,
      target_role: null,
      content: 'Improvements content',
      raw_content: 'Test resume content',
      provider: 'mock',
      model: 'mock-model',
      status: 'success',
      fallback_used: false,
    })

    renderResumePage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '预览优化建议' })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: '预览优化建议' }))

    await waitFor(() => {
      expect(resumeApi.previewImprovements).toHaveBeenCalledWith(1, { target_role: null })
    })
  })

it('calls customizeForJd and shows 进入面试准备 when JD optimization succeeds', async () => {
    const user = userEvent.setup()
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])
    vi.mocked(resumeApi.customizeForJd).mockResolvedValue({
      customized_resume: 'Customized resume content',
      match_report: null,
      session_id: 'test-session-1',
    })

    renderResumePage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'JD 定向优化' })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: 'JD 定向优化' }))

    await waitFor(() => {
      expect(resumeApi.customizeForJd).toHaveBeenCalledWith(1, 1, undefined)
    })
  })
})

describe('WorkspaceShell page structure', () => {
  it('renders page shell with correct heading', () => {
    vi.mocked(resumeApi.list).mockResolvedValue([])
    vi.mocked(jobsApi.list).mockResolvedValue([])

    renderResumePage()

    expect(screen.getByRole('heading', { name: '简历优化', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
})

describe('结果工作台布局', () => {
  it('shows current resume and results overview in first row', async () => {
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])

    renderResumePage()

    await waitFor(() => {
      // 当前简历卡
      expect(screen.getByText('当前简历')).toBeInTheDocument()
      // 结果总览卡
      expect(screen.getByText('结果总览')).toBeInTheDocument()
      // 操作区
      expect(screen.getByText('操作')).toBeInTheDocument()
    })
  })

  it('shows results overview with status indicators', async () => {
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])

    renderResumePage()

    await waitFor(() => {
      expect(screen.getAllByText('简历摘要').length).toBeGreaterThan(0)
      expect(screen.getAllByText('优化建议').length).toBeGreaterThan(0)
      expect(screen.getAllByText('匹配报告').length).toBeGreaterThan(0)
      // 未生成状态
      expect(screen.getAllByText('○ 未生成').length).toBeGreaterThan(0)
    })
  })

  it('shows unified result boundary after generating content', async () => {
    const user = userEvent.setup()
    vi.mocked(resumeApi.list).mockResolvedValue([MOCK_RESUME])
    vi.mocked(jobsApi.list).mockResolvedValue([MOCK_JOB])
    vi.mocked(resumeApi.customizeForJd).mockResolvedValue({
      customized_resume: 'Customized resume content',
      match_report: null,
      session_id: 'test-session-2',
    })

    renderResumePage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'JD 定向优化' })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: 'JD 定向优化' }))

    await waitFor(() => {
      expect(screen.getByText('简历优化结果')).toBeInTheDocument()
      expect(screen.getByText(/已生成 1 \/ 4 项结果/)).toBeInTheDocument()
      expect(screen.getAllByTestId('result-frame')).toHaveLength(1)
    })
  })
})

describe('统一结果区 ResultFrame', () => {
  it('renders success status result area', () => {
    render(<ResultFrame status="success" title="简历摘要">
      <div>摘要内容</div>
    </ResultFrame>)
    expect(screen.getByText(/简历摘要/)).toBeInTheDocument()
    expect(screen.getByText('摘要内容')).toBeInTheDocument()
  })

  it('renders fallback status result area', () => {
    render(<ResultFrame status="fallback" title="简历优化">
      <div>降级内容</div>
    </ResultFrame>)
    expect(screen.getByText(/当前显示的是降级结果/)).toBeInTheDocument()
  })

  it('renders error status result area', () => {
    render(<ResultFrame status="error" title="错误">
      <div>错误内容</div>
    </ResultFrame>)
    expect(screen.getByText(/请重试/)).toBeInTheDocument()
  })

  it('renders loading status result area', () => {
    render(<ResultFrame status="loading" title="加载结果">
      <div data-testid="loading-content">加载中...</div>
    </ResultFrame>)
    expect(screen.getByText(/加载结果/)).toBeInTheDocument()
    expect(screen.getByTestId('loading-content')).toBeInTheDocument()
  })
})
