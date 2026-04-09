import { useState } from 'react'

// Demo data
const DEMO_INTERVIEWS = [
  {
    id: 1,
    type: '前端开发实习',
    date: '2024-01-15',
    score: 85,
    duration: '25 分钟',
    status: '已完成',
    questions: 5,
  },
  {
    id: 2,
    type: '产品经理实习',
    date: '2024-01-10',
    score: 72,
    duration: '20 分钟',
    status: '已完成',
    questions: 4,
  },
]

export function SettingsInterviewsPage() {
  const [interviews] = useState(DEMO_INTERVIEWS)
  const [selectedInterview, setSelectedInterview] = useState<typeof DEMO_INTERVIEWS[0] | null>(null)

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-[var(--color-ink-primary)]">面试记录</h1>
        <p className="mt-0.5 text-sm text-[var(--color-ink-tertiary)]">查看历史练习和 AI 评估报告</p>
      </div>

      {/* Interview List */}
      <div className="space-y-3">
        {interviews.map((interview) => (
          <button
            key={interview.id}
            onClick={() => setSelectedInterview(interview)}
            className="group w-full text-left"
          >
            <div className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-white/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md">
              <div className="flex items-center gap-4">
                {/* Icon */}
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-100 to-blue-100 text-2xl">
                  🎤
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">{interview.type}</h3>
                  <p className="text-xs text-[var(--color-ink-tertiary)]">{interview.date} · {interview.duration}</p>
                </div>
              </div>

              <div className="flex items-center gap-6">
                {/* Score */}
                <div className="text-right">
                  <div className="text-lg font-bold text-[var(--color-accent)]">{interview.score}</div>
                  <div className="text-[10px] text-[var(--color-ink-tertiary)]">综合评分</div>
                </div>

                {/* Questions count */}
                <div className="text-right">
                  <div className="text-sm font-medium text-[var(--color-ink-secondary)]">{interview.questions}</div>
                  <div className="text-[10px] text-[var(--color-ink-tertiary)]">题目数</div>
                </div>

                {/* Status */}
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-600">
                  {interview.status}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Report Modal Placeholder */}
      {selectedInterview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="h-[80vh] w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--color-ink-primary)]">面试报告</h2>
              <button
                onClick={() => setSelectedInterview(null)}
                className="text-2xl text-[var(--color-ink-tertiary)] hover:text-[var(--color-ink-primary)]"
              >
                ×
              </button>
            </div>

            {/* Report content placeholder */}
            <div className="space-y-6">
              {/* Overall score */}
              <div className="flex items-center gap-6 rounded-2xl border border-[var(--color-border)] bg-gradient-to-r from-rose-50 to-orange-50 p-6">
                <div className="text-5xl font-bold text-[var(--color-accent)]">{selectedInterview.score}</div>
                <div>
                  <div className="text-sm font-medium text-[var(--color-ink-primary)]">综合评分</div>
                  <div className="text-xs text-[var(--color-ink-tertiary)]">
                    {selectedInterview.type} · {selectedInterview.date}
                  </div>
                </div>
              </div>

              {/* Dimensions */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">各项得分</h3>
                {['技术表达', '逻辑思维', '项目经验', '应变能力'].map((dim, i) => (
                  <div key={dim} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--color-ink-secondary)]">{dim}</span>
                      <span className="font-medium text-[var(--color-accent)]">{75 + i * 3}分</span>
                    </div>
                    <div className="h-2 rounded-full bg-[var(--color-border)]">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-secondary)]"
                        style={{ width: `${75 + i * 3}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Suggestions */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">改进建议</h3>
                <div className="space-y-2">
                  {[
                    '建议在回答技术问题时，结构化为：问题分析 → 解决方案 → 优化思路',
                    '可以多准备几个项目细节，尤其是性能优化相关的经验',
                    '应变能力较强，但需要加强场景化表达',
                  ].map((sug, i) => (
                    <div key={i} className="flex items-start gap-2 rounded-xl bg-[var(--color-surface-hover)] p-3">
                      <span className="text-[var(--color-accent)]">→</span>
                      <p className="text-sm text-[var(--color-ink-secondary)]">{sug}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
