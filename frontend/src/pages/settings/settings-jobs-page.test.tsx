import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SettingsJobsPage } from './settings-jobs-page'

vi.mock('../../lib/api', () => ({
  jobsApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 1,
        title: '前端开发实习',
        company: '字节跳动',
        location: '北京',
        salary: '400-500/天',
        is_active: true,
        source: 'saved',
        description: '招前端实习生',
        requirements: null,
        company_logo: null,
        work_type: '实习',
        experience: null,
        education: null,
        welfare: null,
        tags: null,
        source_url: null,
        source_id: null,
        publish_date: null,
        deadline: null,
        created_at: '2026-01-01T00:00:00',
        updated_at: '2026-01-01T00:00:00',
      },
      {
        id: 2,
        title: '后端开发实习',
        company: '阿里巴巴',
        location: '杭州',
        salary: '350-450/天',
        is_active: false,
        source: 'saved',
        description: '招后端实习生',
        requirements: null,
        company_logo: null,
        work_type: '实习',
        experience: null,
        education: null,
        welfare: null,
        tags: null,
        source_url: null,
        source_id: null,
        publish_date: null,
        deadline: null,
        created_at: '2026-01-02T00:00:00',
        updated_at: '2026-01-02T00:00:00',
      },
    ]),
    getById: vi.fn().mockResolvedValue({}),
    update: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue(undefined),
    create: vi.fn().mockResolvedValue({}),
    saveExternal: vi.fn().mockResolvedValue({}),
    previewMatch: vi.fn().mockResolvedValue({}),
    persistMatch: vi.fn().mockResolvedValue({}),
    getMatchHistory: vi.fn().mockResolvedValue([]),
    getRecommendedJobs: vi.fn().mockResolvedValue([]),
  },
  readApiError: vi.fn().mockReturnValue('请求失败'),
}))

function renderSettingsJobsPage() {
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
        <SettingsJobsPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SettingsJobsPage', () => {
  it('renders job management page with real data from API', async () => {
    renderSettingsJobsPage()

    expect(screen.getByText('岗位管理')).toBeInTheDocument()
    expect(screen.getByText('管理目标岗位信息')).toBeInTheDocument()

    await screen.findByText('前端开发实习')
    expect(screen.getByText(/400-500/)).toBeInTheDocument()

    await screen.findByText('后端开发实习')
    expect(screen.getByText(/350-450/)).toBeInTheDocument()
  })

  it('shows view, edit, delete action buttons for each job', async () => {
    renderSettingsJobsPage()

    await screen.findByText('前端开发实习')

    const viewButtons = screen.getAllByText('查看')
    expect(viewButtons.length).toBeGreaterThan(0)

    const editButtons = screen.getAllByText('编辑')
    expect(editButtons.length).toBeGreaterThan(0)

    const deleteButtons = screen.getAllByText('删除')
    expect(deleteButtons.length).toBeGreaterThan(0)
  })

  it('marks inactive jobs with ended badge', async () => {
    renderSettingsJobsPage()

    await screen.findByText('后端开发实习')
    expect(screen.getByText('已结束')).toBeInTheDocument()
  })

  it('filter tabs show job counts from real data', async () => {
    renderSettingsJobsPage()

    await screen.findByText('前端开发实习')

    expect(screen.getByText(/全部.*2/)).toBeInTheDocument()
    expect(screen.getByText(/进行中.*1/)).toBeInTheDocument()
    expect(screen.getByText(/已结束.*1/)).toBeInTheDocument()
  })
})
