import { useState } from 'react'

// Demo data
const DEMO_RESUMES = [
  { id: 1, title: '我的简历 v3', fileName: 'resume_v3.pdf', updatedAt: '2024-01-15', isDefault: true },
  { id: 2, title: '产品经理版本', fileName: 'pm_resume.pdf', updatedAt: '2024-01-10', isDefault: false },
  { id: 3, title: '技术岗版本', fileName: 'tech_resume.pdf', updatedAt: '2024-01-05', isDefault: false },
]

export function SettingsResumesPage() {
  const [resumes] = useState(DEMO_RESUMES)
  const [showUpload, setShowUpload] = useState(false)

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--color-ink-primary)]">简历管理</h1>
          <p className="mt-0.5 text-sm text-[var(--color-ink-tertiary)]">上传和管理多版本简历</p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-secondary)] px-4 py-2 text-sm font-medium text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-lg"
        >
          + 上传简历
        </button>
      </div>

      {/* Resume List */}
      <div className="space-y-3">
        {resumes.map((resume) => (
          <div
            key={resume.id}
            className="group flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-white/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md"
          >
            <div className="flex items-center gap-4">
              {/* File icon */}
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-rose-100 to-orange-100 text-2xl">
                📄
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">{resume.title}</h3>
                  {resume.isDefault && (
                    <span className="rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-accent)]">
                      默认
                    </span>
                  )}
                </div>
                <p className="text-xs text-[var(--color-ink-tertiary)]">{resume.fileName}</p>
                <p className="mt-0.5 text-xs text-[var(--color-ink-tertiary)]">更新于 {resume.updatedAt}</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
              <button className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]">
                编辑
              </button>
              <button className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]">
                下载
              </button>
              {!resume.isDefault && (
                <button className="rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--color-error)] hover:bg-red-50">
                  删除
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Upload Modal Placeholder */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
            <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink-primary)]">上传简历</h2>
            <div className="mb-4 rounded-2xl border-2 border-dashed border-[var(--color-border)] p-8 text-center">
              <div className="mb-3 text-4xl">📄</div>
              <p className="text-sm text-[var(--color-ink-secondary)]">拖拽文件或点击上传</p>
              <p className="mt-1 text-xs text-[var(--color-ink-tertiary)]">支持 PDF、DOC、DOCX</p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowUpload(false)}
                className="rounded-xl border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink-secondary)]"
              >
                取消
              </button>
              <button className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white">
                上传
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
