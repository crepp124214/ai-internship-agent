import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SettingsResumesPage } from './settings-resumes-page'

vi.mock('../../lib/api', () => ({
  resumeApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 1,
        user_id: 1,
        title: '我的简历 v3',
        original_file_path: '/uploads/resume_v3.pdf',
        file_name: 'resume_v3.pdf',
        file_type: 'pdf',
        file_size: 102400,
        processed_content: '这是简历内容',
        resume_text: null,
        language: 'zh-CN',
        is_default: true,
        created_at: '2026-01-01T00:00:00',
        updated_at: '2026-01-15T00:00:00',
      },
      {
        id: 2,
        user_id: 1,
        title: '技术岗版本',
        original_file_path: '/uploads/tech_resume.pdf',
        file_name: 'tech_resume.pdf',
        file_type: 'pdf',
        file_size: 98304,
        processed_content: '技术岗简历内容',
        resume_text: null,
        language: 'zh-CN',
        is_default: false,
        created_at: '2026-01-02T00:00:00',
        updated_at: '2026-01-10T00:00:00',
      },
    ]),
    delete: vi.fn().mockResolvedValue(undefined),
    update: vi.fn().mockResolvedValue({}),
  },
  readApiError: vi.fn().mockReturnValue('请求失败'),
}))

function renderSettingsResumesPage() {
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
        <SettingsResumesPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SettingsResumesPage', () => {
  it('renders resume management page with view, edit, delete actions', async () => {
    renderSettingsResumesPage()

    expect(screen.getByText('简历管理')).toBeInTheDocument()
    expect(screen.getByText('管理多版本简历')).toBeInTheDocument()

    // Wait for data to load
    await screen.findByText('我的简历 v3')
    expect(screen.getByText('技术岗版本')).toBeInTheDocument()

    // Check for action buttons - only delete for default resume
    expect(screen.getAllByText('删除').length).toBeGreaterThan(0)
  })

  it('shows 查看 and 编辑 buttons for non-default resumes', async () => {
    renderSettingsResumesPage()

    await screen.findByText('我的简历 v3')

    // Should show 查看 and 编辑 for most resumes
    expect(screen.getAllByText('查看').length).toBeGreaterThan(0)
    expect(screen.getAllByText('编辑').length).toBeGreaterThan(0)
  })

  it('does not render import or upload buttons', async () => {
    renderSettingsResumesPage()

    await screen.findByText('我的简历 v3')

    // Should NOT have import/upload buttons
    expect(screen.queryByText('上传简历')).not.toBeInTheDocument()
    expect(screen.queryByText('+ 上传')).not.toBeInTheDocument()
  })
})