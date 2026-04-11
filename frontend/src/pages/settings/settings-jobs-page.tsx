import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { jobsApi, readApiError, type Job, type JobUpdatePayload } from '../../lib/api'

type FilterTab = 'all' | 'active' | 'ended'

export function SettingsJobsPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<FilterTab>('all')
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [viewingJob, setViewingJob] = useState<Job | null>(null)

  const jobsQuery = useQuery({
    queryKey: ['settings', 'jobs'],
    queryFn: jobsApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: (jobId: number) => jobsApi.delete(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'jobs'] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ jobId, payload }: { jobId: number; payload: JobUpdatePayload }) =>
      jobsApi.update(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'jobs'] })
      setEditingJob(null)
    },
  })

  const jobs: Job[] = jobsQuery.data ?? []

  const filteredJobs = jobs.filter((job) => {
    if (filter === 'active') return job.is_active
    if (filter === 'ended') return !job.is_active
    return true
  })

  const activeCount = jobs.filter((j) => j.is_active).length
  const endedCount = jobs.filter((j) => !j.is_active).length

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6">
        <div>
          <h1 className="text-xl font-bold text-[var(--color-ink-primary)]">岗位管理</h1>
          <p className="mt-0.5 text-sm text-[var(--color-ink-tertiary)]">管理目标岗位信息</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="mb-5 flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            filter === 'all'
              ? 'bg-[var(--color-accent)] text-white'
              : 'border border-[var(--color-border)] bg-white text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]'
          }`}
        >
          全部 ({jobs.length})
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            filter === 'active'
              ? 'bg-[var(--color-accent)] text-white'
              : 'border border-[var(--color-border)] bg-white text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]'
          }`}
        >
          进行中 ({activeCount})
        </button>
        <button
          onClick={() => setFilter('ended')}
          className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
            filter === 'ended'
              ? 'bg-[var(--color-accent)] text-white'
              : 'border border-[var(--color-border)] bg-white text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]'
          }`}
        >
          已结束 ({endedCount})
        </button>
      </div>

      {/* Loading / Error states */}
      {jobsQuery.isLoading && (
        <div className="flex items-center justify-center py-12">
          <span className="text-sm text-[var(--color-ink-tertiary)]">加载中...</span>
        </div>
      )}

      {jobsQuery.isError && (
        <div className="flex items-center justify-center py-12">
          <span className="text-sm text-[var(--color-error)]">{readApiError(jobsQuery.error)}</span>
        </div>
      )}

      {/* Empty state */}
      {!jobsQuery.isLoading && !jobsQuery.isError && filteredJobs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12">
          <span className="text-4xl mb-3">💼</span>
          <p className="text-sm text-[var(--color-ink-tertiary)]">暂无岗位</p>
        </div>
      )}

      {/* Jobs List */}
      {!jobsQuery.isLoading && !jobsQuery.isError && filteredJobs.length > 0 && (
        <div className="space-y-3">
          {filteredJobs.map((job) => (
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
                    {!job.is_active && (
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
                <button
                  onClick={() => setViewingJob(job)}
                  className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]"
                >
                  查看
                </button>
                <button
                  onClick={() => setEditingJob(job)}
                  className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]"
                >
                  编辑
                </button>
                <button
                  onClick={() => {
                    if (window.confirm(`确认删除岗位「${job.title}」吗？`)) {
                      deleteMutation.mutate(job.id)
                    }
                  }}
                  className="rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--color-error)] hover:bg-red-50"
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingJob && (
        <JobEditModal
          job={editingJob}
          onClose={() => setEditingJob(null)}
          onSave={(payload) => updateMutation.mutate({ jobId: editingJob.id, payload })}
          isSaving={updateMutation.isPending}
          saveError={updateMutation.isError ? readApiError(updateMutation.error) : null}
        />
      )}

      {/* View Modal */}
      {viewingJob && (
        <JobViewModal job={viewingJob} onClose={() => setViewingJob(null)} />
      )}
    </div>
  )
}

// --- Sub-components ---

function JobEditModal({
  job,
  onClose,
  onSave,
  isSaving,
  saveError,
}: {
  job: Job
  onClose: () => void
  onSave: (payload: JobUpdatePayload) => void
  isSaving: boolean
  saveError: string | null
}) {
  const [title, setTitle] = useState(job.title)
  const [company, setCompany] = useState(job.company)
  const [location, setLocation] = useState(job.location)
  const [description, setDescription] = useState(job.description ?? '')
  const [salary, setSalary] = useState(job.salary ?? '')
  const [isActive, setIsActive] = useState(job.is_active)

  const handleSave = () => {
    onSave({
      title,
      company,
      location,
      description,
      salary: salary || undefined,
      is_active: isActive,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink-primary)]">编辑岗位</h2>
        {saveError && (
          <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-[var(--color-error)]">
            {saveError}
          </div>
        )}
        <div className="mb-4 space-y-3">
          <input
            type="text"
            placeholder="岗位名称"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
          />
          <input
            type="text"
            placeholder="公司名称"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
          />
          <input
            type="text"
            placeholder="工作地点"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
          />
          <textarea
            placeholder="岗位描述"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] resize-none"
          />
          <input
            type="text"
            placeholder="薪资"
            value={salary}
            onChange={(e) => setSalary(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
          />
          <div className="flex items-center gap-3">
            <label className="text-sm text-[var(--color-ink-secondary)]">状态：</label>
            <button
              type="button"
              onClick={() => setIsActive(true)}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                isActive
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              进行中
            </button>
            <button
              type="button"
              onClick={() => setIsActive(false)}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                !isActive
                  ? 'bg-gray-100 text-gray-500'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              已结束
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
            onClick={handleSave}
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

function JobViewModal({ job, onClose }: { job: Job; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-ink-primary)]">{job.title}</h2>
            <p className="mt-0.5 text-sm text-[var(--color-ink-secondary)]">{job.company} · {job.location}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[var(--color-ink-tertiary)] hover:bg-gray-100"
          >
            ✕
          </button>
        </div>
        <div className="mb-4 space-y-2 text-sm">
          {job.salary && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">薪资：</span>
              <span className="text-[var(--color-accent)] font-medium">{job.salary}</span>
            </div>
          )}
          {job.work_type && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">工作类型：</span>
              <span>{job.work_type}</span>
            </div>
          )}
          {job.experience && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">经验要求：</span>
              <span>{job.experience}</span>
            </div>
          )}
          {job.education && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">学历要求：</span>
              <span>{job.education}</span>
            </div>
          )}
          {job.welfare && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">福利：</span>
              <span>{job.welfare}</span>
            </div>
          )}
          {job.tags && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">标签：</span>
              <span>{job.tags}</span>
            </div>
          )}
          {job.source_url && (
            <div className="flex gap-2">
              <span className="text-[var(--color-ink-tertiary)]">链接：</span>
              <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-[var(--color-accent)] underline">
                {job.source_url}
              </a>
            </div>
          )}
          <div className="flex gap-2">
            <span className="text-[var(--color-ink-tertiary)]">状态：</span>
            <span className={job.is_active ? 'text-green-600' : 'text-gray-500'}>
              {job.is_active ? '进行中' : '已结束'}
            </span>
          </div>
        </div>
        {job.description && (
          <div className="mb-4">
            <h3 className="mb-1 text-xs font-medium text-[var(--color-ink-tertiary)]">职位描述</h3>
            <p className="whitespace-pre-wrap rounded-xl bg-gray-50 p-3 text-sm text-[var(--color-ink-secondary)]">
              {job.description}
            </p>
          </div>
        )}
        {job.requirements && (
          <div className="mb-4">
            <h3 className="mb-1 text-xs font-medium text-[var(--color-ink-tertiary)]">职位要求</h3>
            <p className="whitespace-pre-wrap rounded-xl bg-gray-50 p-3 text-sm text-[var(--color-ink-secondary)]">
              {job.requirements}
            </p>
          </div>
        )}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="rounded-xl border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink-secondary)]"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  )
}
