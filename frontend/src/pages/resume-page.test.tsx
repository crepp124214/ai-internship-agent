import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { resumeApi } from '../lib/api'
import { ResumePage } from './resume-page'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')

  return {
    ...actual,
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

function renderResumePage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <ResumePage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ResumePage', () => {
  it('imports a local text resume, creates it, and writes the contents back', async () => {
    const user = userEvent.setup()
    const mockedResumeApi = vi.mocked(resumeApi)
    let resumes = [] as Array<{
      id: number
      user_id: number
      title: string
      original_file_path: string
      file_name: string
      file_type: string
      file_size: number | null
      processed_content: string | null
      resume_text: string | null
      language: string
      is_default: boolean
      created_at: string
      updated_at: string
    }>

    mockedResumeApi.list.mockImplementation(async () => resumes)
    mockedResumeApi.create.mockImplementation(async () => {
      const createdResume = {
        id: 101,
        user_id: 1,
        title: '导入测试简历',
        original_file_path: 'imports/101-alice-md.md',
        file_name: 'alice.md',
        file_type: 'text/markdown',
        file_size: 42,
        processed_content: null,
        resume_text: null,
        language: 'zh',
        is_default: false,
        created_at: '2026-04-02T00:00:00Z',
        updated_at: '2026-04-02T00:00:00Z',
      }
      resumes = [createdResume]
      return createdResume
    })
    mockedResumeApi.update.mockImplementation(async () => {
      const updatedResume = {
        id: 101,
        user_id: 1,
        title: '导入测试简历',
        original_file_path: 'imports/101-alice-md.md',
        file_name: 'alice.md',
        file_type: 'text/markdown',
        file_size: 42,
        processed_content: '# Resume\nSenior frontend engineer',
        resume_text: '# Resume\nSenior frontend engineer',
        language: 'zh',
        is_default: false,
        created_at: '2026-04-02T00:00:00Z',
        updated_at: '2026-04-02T00:00:01Z',
      }
      resumes = [updatedResume]
      return updatedResume
    })

    renderResumePage()

    await user.type(screen.getByLabelText('新建简历'), '导入测试简历')
    await user.upload(
      screen.getByLabelText(/导入本地文本简历/),
      new File(['# Resume\nSenior frontend engineer'], 'alice.md', { type: 'text/markdown' }),
    )
    await user.click(screen.getByRole('button', { name: '导入并创建' }))

    await waitFor(() =>
      expect(mockedResumeApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: '导入测试简历',
          file_path: expect.stringContaining('alice.md'),
        }),
      ),
    )
    await waitFor(() =>
      expect(mockedResumeApi.update).toHaveBeenCalledWith(
        101,
        expect.objectContaining({
          processed_content: '# Resume\nSenior frontend engineer',
          resume_text: '# Resume\nSenior frontend engineer',
        }),
      ),
    )

    expect(screen.getByText('简历导入并写入成功')).toBeInTheDocument()
  })
})
