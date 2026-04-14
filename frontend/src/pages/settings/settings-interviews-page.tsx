import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'

import { EmptyHint } from '../page-primitives'
import { interviewApi, readApiError, type InterviewSession, type ReviewReport, type InterviewQuestionSet } from '../../lib/api'

export function SettingsInterviewsPage() {
  const navigate = useNavigate()

  const sessionsQuery = useQuery<InterviewSession[], Error>({
    queryKey: ['interview', 'sessions'],
    queryFn: () => interviewApi.listSessions(),
  })

  const questionSetsQuery = useQuery<InterviewQuestionSet[], Error>({
    queryKey: ['interview', 'question-sets'],
    queryFn: () => interviewApi.listQuestionSets(),
  })

  const [selectedSession, setSelectedSession] = useState<InterviewSession | null>(null)
  const [report, setReport] = useState<ReviewReport | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState<string | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)
  const sessions = sessionsQuery.data ?? []
  const questionSets = questionSetsQuery.data ?? []

  useEffect(() => {
    if (sessionsQuery.error) {
      setSessionsError(readApiError(sessionsQuery.error))
      return
    }
    setSessionsError(null)
  }, [sessionsQuery.error])

  const handleSelectSession = async (session: InterviewSession) => {
    setSelectedSession(session)
    setReport(null)
    setReportError(null)
    if (session.completed) {
      setReportLoading(true)
      try {
        const data = await interviewApi.coachGetReport(session.id)
        setReport(data.review_report)
      } catch (error) {
        setReportError(readApiError(error))
      } finally {
        setReportLoading(false)
      }
    }
  }

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--color-ink-primary)]">面试记录</h1>
          <p className="mt-0.5 text-sm text-[var(--color-ink-tertiary)]">查看历史练习和 AI 评估报告</p>
        </div>
        {questionSets.length > 0 && (
          <button
            onClick={() => {
              const firstSet = questionSets[0]
              navigate('/interview', { state: { questionSetId: firstSet.id } })
            }}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-secondary)] px-4 py-2 text-sm font-medium text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-lg"
          >
            从题集开始练习
          </button>
        )}
      </div>

      {/* Interview List */}
      {sessionsError ? (
        <div className="py-12 text-center text-sm text-[var(--color-ink)]">
          加载面试记录失败：{sessionsError}
        </div>
      ) : sessionsQuery.isLoading ? (
        <div className="py-12 text-center text-sm text-[var(--color-ink-tertiary)]">加载中...</div>
      ) : sessions.length > 0 ? (
        <div className="space-y-3">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => handleSelectSession(session)}
              className="group w-full text-left"
            >
              <div className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-white/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md">
                <div className="flex items-center gap-4">
                  {/* Icon */}
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-100 to-blue-100 text-2xl">
                    🎤
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">
                      {session.session_type === 'technical' ? '技术面试' : session.session_type}
                    </h3>
                    <p className="text-xs text-[var(--color-ink-tertiary)]">
                      {new Date(session.created_at).toLocaleDateString('zh-CN')}
                      {session.duration ? ` · ${session.duration} 分钟` : ''}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  {/* Score */}
                  {session.average_score != null ? (
                    <div className="text-right">
                      <div className="text-lg font-bold text-[var(--color-accent)]">
                        {Math.round(session.average_score)}
                      </div>
                      <div className="text-[10px] text-[var(--color-ink-tertiary)]">综合评分</div>
                    </div>
                  ) : (
                    <div className="text-right">
                      <div className="text-sm font-medium text-[var(--color-ink-tertiary)]">—</div>
                      <div className="text-[10px] text-[var(--color-ink-tertiary)]">综合评分</div>
                    </div>
                  )}

                  {/* Questions count */}
                  <div className="text-right">
                    <div className="text-sm font-medium text-[var(--color-ink-secondary)]">
                      {session.total_questions ?? 0}
                    </div>
                    <div className="text-[10px] text-[var(--color-ink-tertiary)]">题目数</div>
                  </div>

                  {/* Status */}
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      session.completed
                        ? 'bg-emerald-50 text-emerald-600'
                        : 'bg-amber-50 text-amber-600'
                    }`}
                  >
                    {session.completed ? '已完成' : '进行中'}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <EmptyHint>暂无面试记录，去面试准备页面开始练习吧。</EmptyHint>
      )}

      {/* Question Sets Section */}
      {questionSets.length > 0 && (
        <div className="mt-8 border-t border-[var(--color-border)] pt-6">
          <div className="mb-4">
            <h2 className="text-base font-semibold text-[var(--color-ink-primary)]">题集复用 {questionSets.length} 个</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {questionSets.map((qs) => (
              <button
                key={qs.id}
                onClick={() => navigate('/interview', { state: { questionSetId: qs.id } })}
                className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-secondary)] hover:bg-[var(--color-surface-hover)]"
              >
                {qs.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Report Modal */}
      {selectedSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="h-[80vh] w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--color-ink-primary)]">面试报告</h2>
              <button
                onClick={() => {
                  setSelectedSession(null)
                  setReport(null)
                }}
                className="text-2xl text-[var(--color-ink-tertiary)] hover:text-[var(--color-ink-primary)]"
              >
                ×
              </button>
            </div>

            {reportLoading ? (
              <div className="py-12 text-center text-sm text-[var(--color-ink-tertiary)]">报告加载中...</div>
            ) : reportError ? (
              <div className="py-12 text-center text-sm text-[var(--color-ink)]">
                加载报告失败：{reportError}
              </div>
            ) : report ? (
              <div className="space-y-6">
                {/* Overall score */}
                <div className="flex items-center gap-6 rounded-2xl border border-[var(--color-border)] bg-gradient-to-r from-rose-50 to-orange-50 p-6">
                  <div className="text-5xl font-bold text-[var(--color-accent)]">{report.overall_score}</div>
                  <div>
                    <div className="text-sm font-medium text-[var(--color-ink-primary)]">综合评分</div>
                    <div className="text-xs text-[var(--color-ink-tertiary)]">
                      {selectedSession.session_type === 'technical' ? '技术面试' : selectedSession.session_type} ·
                      {new Date(selectedSession.created_at).toLocaleDateString('zh-CN')}
                    </div>
                  </div>
                </div>

                {/* Overall comment */}
                <p className="text-sm text-[var(--color-ink-secondary)]">{report.overall_comment}</p>

                {/* Dimensions */}
                {report.dimensions && report.dimensions.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">各项得分</h3>
                    {report.dimensions.map((dim, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-[var(--color-ink-secondary)]">{dim.name}</span>
                          <span className="font-medium text-[var(--color-accent)]">
                            {dim.score}分 · {dim.stars}星
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-[var(--color-border)]">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-secondary)]"
                            style={{ width: `${dim.score}%` }}
                          />
                        </div>
                        <p className="text-xs text-[var(--color-ink-tertiary)]">{dim.suggestion}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Suggestions */}
                {report.improvement_suggestions && report.improvement_suggestions.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-[var(--color-ink-primary)]">改进建议</h3>
                    <div className="space-y-2">
                      {report.improvement_suggestions.map((sug, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 rounded-xl bg-[var(--color-surface-hover)] p-3"
                        >
                          <span className="text-[var(--color-accent)]">→</span>
                          <p className="text-sm text-[var(--color-ink-secondary)]">{sug}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-sm text-[var(--color-ink-tertiary)]">
                该面试还未完成，无法查看报告。
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
