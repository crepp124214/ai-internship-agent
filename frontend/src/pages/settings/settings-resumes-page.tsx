import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { EmptyHint } from '../page-primitives'
import { resumeApi, readApiError, type Resume, type ResumeUpdatePayload } from '../../lib/api'

export function SettingsResumesPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [viewingResume, setViewingResume] = useState<Resume | null>(null)
  const [editingResume, setEditingResume] = useState<Resume | null>(null)

  const { data: resumes = [], isLoading } = useQuery<Resume[], Error>({
    queryKey: ['resumes'],
    queryFn: () => resumeApi.list(),
  })

  const deleteMutation = useMutation({
    mutationFn: (resumeId: number) => resumeApi.delete(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
    },
    onError: (err) => {
      setError(readApiError(err))
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ResumeUpdatePayload }) =>
      resumeApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      setEditingResume(null)
    },
  })

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6">
        <div>
          <h1 className="text-xl font-bold text-[var(--color-ink-primary)]">简历管理</h1>
          <p className="mt-0.5 text-sm text-[var(--color-ink-tertiary)]">管理多版本简历</p>
        </div>
      </div>

      {/* Resume List */}
      {error && (
        <div className="mb-4 rounded-xl bg-red-50 p-4 text-sm text-[var(--color-error)]">
          {error}
        </div>
      )}
      {isLoading ? (
        <div className="py-12 text-center text-sm text-[var(--color-ink-tertiary)]">加载中...</div>
      ) : resumes.length > 0 ? (
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
                    {resume.is_default && (
                      <span className="rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-accent)]">
                        默认
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--color-ink-tertiary)]">{resume.file_name}</p>
                  <p className="mt-0.5 text-xs text-[var(--color-ink-tertiary)]">
                    更新于 {new Date(resume.updated_at).toLocaleDateString('zh-CN')}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  onClick={() => setViewingResume(resume)}
                  className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]"
                >
                  查看
                </button>
                <button
                  onClick={() => setEditingResume(resume)}
                  className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]"
                >
                  编辑
                </button>
                {!resume.is_default && (
                  <button
                    className="rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--color-error)] hover:bg-red-50"
                    onClick={() => {
                      if (confirm('确定要删除这份简历吗？')) {
                        deleteMutation.mutate(resume.id)
                      }
                    }}
                  >
                    删除
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyHint>暂无简历，请前往设置中心导入简历。</EmptyHint>
      )}

      {/* View Modal */}
      {viewingResume && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-[var(--color-ink-primary)]">{viewingResume.title}</h2>
                <p className="mt-0.5 text-sm text-[var(--color-ink-secondary)]">{viewingResume.file_name}</p>
              </div>
              <button
                onClick={() => setViewingResume(null)}
                className="rounded-lg p-1 text-[var(--color-ink-tertiary)] hover:bg-gray-100"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex gap-2">
                <span className="text-[var(--color-ink-tertiary)]">状态：</span>
                <span className={viewingResume.is_default ? 'text-green-600' : 'text-gray-500'}>
                  {viewingResume.is_default ? '默认' : '普通'}
                </span>
              </div>
              <div className="flex gap-2">
                <span className="text-[var(--color-ink-tertiary)]">更新于：</span>
                <span>{new Date(viewingResume.updated_at).toLocaleString('zh-CN')}</span>
              </div>
              {viewingResume.processed_content && (
                <div>
                  <h3 className="mb-1 text-xs font-medium text-[var(--color-ink-tertiary)]">简历内容</h3>
                  <div className="whitespace-pre-wrap rounded-xl bg-gray-50 p-3 text-sm text-[var(--color-ink-secondary)] max-h-60 overflow-y-auto">
                    {viewingResume.processed_content}
                  </div>
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setViewingResume(null)}
                className="rounded-xl border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink-secondary)]"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingResume && (
        <ResumeEditModal
          resume={editingResume}
          onClose={() => setEditingResume(null)}
          onSave={(payload) => updateMutation.mutate({ id: editingResume.id, payload })}
          isSaving={updateMutation.isPending}
        />
      )}
    </div>
  )
}

// --- Sub-components ---

function ResumeEditModal({
  resume,
  onClose,
  onSave,
  isSaving,
}: {
  resume: Resume
  onClose: () => void
  onSave: (payload: ResumeUpdatePayload) => void
  isSaving: boolean
}) {
  const [title, setTitle] = useState(resume.title)
  const [isDefault, setIsDefault] = useState(resume.is_default)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink-primary)]">编辑简历</h2>
        <div className="mb-4 space-y-3">
          <input
            type="text"
            placeholder="简历标题"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
          />
          <div className="flex items-center gap-3">
            <label className="text-sm text-[var(--color-ink-secondary)]">设为默认：</label>
            <button
              type="button"
              onClick={() => setIsDefault(true)}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                isDefault ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'
              }`}
            >
              是
            </button>
            <button
              type="button"
              onClick={() => setIsDefault(false)}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                !isDefault ? 'bg-gray-100 text-gray-500' : 'bg-gray-100 text-gray-400'
              }`}
            >
              否
            </button>
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-xl border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink-secondary)]"
          >
            取消
          </button>
          <button
            onClick={() => onSave({ title, is_default: isDefault })}
            disabled={isSaving}
            className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {isSaving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}
