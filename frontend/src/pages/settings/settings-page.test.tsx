import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { clearStoredToken, setStoredToken } from '../../auth/auth-storage'
import { SettingsPage } from './settings-page'

// Use vi.hoisted to create mock functions that can be accessed before initialization
const { mockGetUserLlmConfigs } = vi.hoisted(() => ({
  mockGetUserLlmConfigs: vi.fn().mockResolvedValue([]),
}))

// Mock API
vi.mock('../../lib/api', () => ({
  getUserLlmConfigs: mockGetUserLlmConfigs,
}))

// Mock react-router
vi.mock('react-router', () => ({
  useNavigate: () => vi.fn(),
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

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearStoredToken()
    vi.stubGlobal('fetch', vi.fn())
  })

  function renderSettingsPage(configs: { agent: string; provider: string; model: string; temperature: number }[] = []) {
    mockGetUserLlmConfigs.mockResolvedValue(configs)
    const queryClient = createTestQueryClient()

    return render(
      <MemoryRouter>
        <QueryClientProvider client={queryClient}>
          <SettingsPage />
        </QueryClientProvider>
      </MemoryRouter>,
    )
  }

  it('renders page shell with title', async () => {
    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '设置中心' })).toBeInTheDocument()
    })
    expect(screen.getByText('系统控制中心')).toBeInTheDocument()
  })

  it('shows configuration and status panels in first row', async () => {
    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText('全局配置')).toBeInTheDocument()
      expect(screen.getByText('系统状态')).toBeInTheDocument()
    })
  })

  it('shows tool import panel and data management entries', async () => {
    renderSettingsPage()

    await waitFor(() => {
      // 工具导入面板（第二层）
      expect(screen.getByText('工具导入')).toBeInTheDocument()
      expect(screen.getByText('导入简历')).toBeInTheDocument()
      expect(screen.getByText('导入岗位')).toBeInTheDocument()
      // 数据管理（第三层）
      expect(screen.getByText('数据管理')).toBeInTheDocument()
      expect(screen.getByText('简历管理')).toBeInTheDocument()
      expect(screen.getByText('岗位管理')).toBeInTheDocument()
      expect(screen.getByText('面试记录')).toBeInTheDocument()
    })
  })

  it('shows agent status when configs exist', async () => {
    const configs = [
      { agent: 'resume_agent', provider: 'openai', model: 'gpt-4o-mini', temperature: 0.7 },
      { agent: 'job_agent', provider: 'openai', model: 'gpt-4o-mini', temperature: 0.7 },
      { agent: 'interview_agent', provider: 'openai', model: 'gpt-4o-mini', temperature: 0.7 },
    ]

    renderSettingsPage(configs)

    await waitFor(() => {
      expect(screen.getByText(/3 \/ 3 个 Agent/)).toBeInTheDocument()
      expect(screen.getByText('简历 Agent')).toBeInTheDocument()
      expect(screen.getByText('岗位 Agent')).toBeInTheDocument()
      expect(screen.getByText('面试 Agent')).toBeInTheDocument()
    })
  })

  it('shows "未配置" when no configs exist', async () => {
    renderSettingsPage([])

    await waitFor(() => {
      expect(screen.getByText(/0 \/ 3 个 Agent/)).toBeInTheDocument()
      // 多个元素包含"未配置"，使用 getAllByText
      expect(screen.getAllByText('未配置').length).toBeGreaterThan(0)
    })
  })

  it('uses stored auth token when uploading from unified import panel', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue({
      json: async () => ({ success: true, resume_id: 42 }),
    } as Response)
    setStoredToken('live-token')

    renderSettingsPage()
    expect(screen.getByText('未选择文件')).toBeInTheDocument()
    const fileInput = screen.getByLabelText('选择文件') as HTMLInputElement
    const file = new File(['resume'], 'resume.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    await userEvent.upload(fileInput, file)
    await userEvent.click(screen.getByRole('button', { name: '上传' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/import/resume',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer live-token',
          }),
        }),
      )
    })
  })

  it('renders native file input in the unified import panel', async () => {
    renderSettingsPage()

    expect(screen.getByLabelText('选择文件')).toBeInTheDocument()
  })

  it('shows the selected file name in the unified import panel', async () => {
    renderSettingsPage()
    const fileInput = screen.getByLabelText('选择文件') as HTMLInputElement

    const file = new File(['resume'], 'resume.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })

    await userEvent.upload(fileInput, file)

    expect(screen.getByText('resume.docx')).toBeInTheDocument()
  })
})
