import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { clearStoredToken, setStoredToken } from '../../auth/auth-storage'
import { DataImportModal } from './DataImportModal'

describe('DataImportModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearStoredToken()
    vi.stubGlobal('fetch', vi.fn())
  })

  it('uses stored auth token when uploading resume', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue({
      json: async () => ({ success: true, resume_id: 7 }),
    } as Response)
    setStoredToken('modal-token')

    const onImportSuccess = vi.fn()
    render(
      <DataImportModal isOpen onClose={vi.fn()} onImportSuccess={onImportSuccess} />,
    )

    const fileInput = screen.getByLabelText('选择文件') as HTMLInputElement
    expect(screen.getByText('未选择文件')).toBeInTheDocument()
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
            Authorization: 'Bearer modal-token',
          }),
        }),
      )
    })

    await waitFor(() => {
      expect(onImportSuccess).toHaveBeenCalled()
      expect(screen.getByText('导入成功！')).toBeInTheDocument()
    })
  })

  it('renders native file input for file selection', async () => {
    render(<DataImportModal isOpen onClose={vi.fn()} />)

    expect(screen.getByLabelText('选择文件')).toBeInTheDocument()
  })

  it('shows the selected file name after choosing a file', async () => {
    render(<DataImportModal isOpen onClose={vi.fn()} />)

    const fileInput = screen.getByLabelText('选择文件') as HTMLInputElement

    const file = new File(['resume'], 'resume.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })

    await userEvent.upload(fileInput, file)

    expect(screen.getByText('resume.docx')).toBeInTheDocument()
  })
})
