import { useState } from 'react'

// Demo data
const DEMO_JOBS = [
  { id: 1, title: '前端开发实习', company: '字节跳动', location: '北京', salary: '400-500/天', isActive: true },
  { id: 2, title: '产品经理实习', company: '腾讯', location: '深圳', salary: '200-300/天', isActive: true },
  { id: 3, title: '后端开发实习', company: '阿里巴巴', location: '杭州', salary: '350-450/天', isActive: false },
  { id: 4, title: '算法实习', company: '美团', location: '北京', salary: '400-600/天', isActive: true },
  { id: 5, title: '数据分析师', company: '拼多多', location: '上海', salary: '300-400/天', isActive: true },
]

export function SettingsJobsPage() {
  const [jobs] = useState(DEMO_JOBS)
  const [showImport, setShowImport] = useState(false)

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--color-ink-primary)]">岗位管理</h1>
          <p className="mt-0.5 text-sm text-[var(--color-ink-tertiary)]">导入和管理目标岗位信息</p>
        </div>
        <button
          onClick={() => setShowImport(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-secondary)] px-4 py-2 text-sm font-medium text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-lg"
        >
          + 导入岗位
        </button>
      </div>

      {/* Filter tabs */}
      <div className="mb-5 flex gap-2">
        <button className="rounded-full bg-[var(--color-accent)] px-4 py-1.5 text-xs font-medium text-white">
          全部 ({jobs.length})
        </button>
        <button className="rounded-full border border-[var(--color-border)] bg-white px-4 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)]">
          进行中 (4)
        </button>
        <button className="rounded-full border border-[var(--color-border)] bg-white px-4 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)]">
          已结束 (1)
        </button>
      </div>

      {/* Jobs List */}
      <div className="space-y-3">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="group flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-white/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md"
          >
            <div className="flex items-center gap-4">
              {/* Company icon */}
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 to-purple-100 text-2xl">
                💼
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">{job.title}</h3>
                  {!job.isActive && (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500">
                      已结束
                    </span>
                  )}
                </div>
                <p className="text-xs text-[var(--color-ink-secondary)]">{job.company} · {job.location}</p>
                {job.salary && (
                  <p className="mt-0.5 text-xs font-medium text-[var(--color-accent)]">{job.salary}</p>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
              <button className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]">
                查看
              </button>
              <button className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]">
                匹配
              </button>
              <button className="rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--color-error)] hover:bg-red-50">
                删除
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Import Modal Placeholder */}
      {showImport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
            <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink-primary)]">导入岗位</h2>
            <div className="mb-4 space-y-3">
              <button className="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] p-4 text-left transition-all hover:bg-[var(--color-surface-hover)]">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🔗</span>
                  <div>
                    <p className="text-sm font-medium text-[var(--color-ink-primary)]">粘贴链接</p>
                    <p className="text-xs text-[var(--color-ink-tertiary)]">从招聘网站复制职位链接</p>
                  </div>
                </div>
                <span className="text-[var(--color-ink-tertiary)]">→</span>
              </button>
              <button className="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] p-4 text-left transition-all hover:bg-[var(--color-surface-hover)]">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📄</span>
                  <div>
                    <p className="text-sm font-medium text-[var(--color-ink-primary)]">上传文件</p>
                    <p className="text-xs text-[var(--color-ink-tertiary)]">支持 JSON、CSV 格式</p>
                  </div>
                </div>
                <span className="text-[var(--color-ink-tertiary)]">→</span>
              </button>
              <button className="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] p-4 text-left transition-all hover:bg-[var(--color-surface-hover)]">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">✏️</span>
                  <div>
                    <p className="text-sm font-medium text-[var(--color-ink-primary)]">手动填写</p>
                    <p className="text-xs text-[var(--color-ink-tertiary)]">逐个输入岗位信息</p>
                  </div>
                </div>
                <span className="text-[var(--color-ink-tertiary)]">→</span>
              </button>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => setShowImport(false)}
                className="rounded-xl border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink-secondary)]"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
