import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { EmptyHint } from '../page-primitives'
import { resumeApi, readApiError, type Resume } from '../../lib/api'

export function SettingsResumesPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

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
    </div>
  )
}
