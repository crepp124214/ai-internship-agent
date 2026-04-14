import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  interviewApi,
  jobsApi,
  readApiError,
  resumeApi,
  type InterviewQuestionSet,
  type ReviewReport,
} from '../lib/api'
import { ChatBubble } from './components/ChatBubble'
import {
  FormField,
  PrimaryButton,
  ResultFrame,
  SecondaryButton,
  Select,
  Textarea,
  WorkspaceShell,
} from './page-primitives'

const SCORE_PLACEHOLDER_TEXT = '评分暂不可用'

function formatImmediateScoreFeedback(score: number, feedback?: string | null) {
  const normalizedFeedback = feedback?.trim()

  if (!normalizedFeedback || normalizedFeedback.includes(SCORE_PLACEHOLDER_TEXT)) {
    return `本题得分：${score}分`
  }

  return `本题得分：${score}分 - ${normalizedFeedback}`
}

export function InterviewPage() {
  const location = useLocation()
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const questionSetsQuery = useQuery({ queryKey: ['interview', 'question-sets'], queryFn: interviewApi.listQuestionSets })
  const sessionsQuery = useQuery({ queryKey: ['interview', 'sessions'], queryFn: interviewApi.listSessions })
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [selectedQuestionSetId, setSelectedQuestionSetId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  // Coach mode state
  const [coachActive, setCoachActive] = useState(false)
  const [coachSessionId, setCoachSessionId] = useState<number | null>(null)
  const [coachMessages, setCoachMessages] = useState<Array<{role: 'ai' | 'user', message: string, score?: number | null}>>([])
  const [coachAnswer, setCoachAnswer] = useState('')
  const [coachFeedback, setCoachFeedback] = useState<string | null>(null)
  const [coachReport, setCoachReport] = useState<{ review_report: ReviewReport; average_score: number } | null>(null)
  const [inFollowup, setInFollowup] = useState(false)

  const latestCompletedSession =
    sessionsQuery.data
      ?.filter((session) => Boolean(session.completed))
      .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0] ?? null

  const latestReportQuery = useQuery({
    queryKey: ['interview', 'coach-report', latestCompletedSession?.id],
    queryFn: () => interviewApi.coachGetReport(latestCompletedSession!.id),
    enabled: Boolean(latestCompletedSession),
  })

  // 从 resume / settings-interviews 跳转过来的上下文
  useEffect(() => {
    const state = location.state as {
      fromResume?: { jobId: number; resumeId: number }
      questionSetId?: number
    } | null

    if (state?.fromResume) {
      setSelectedJobId(state.fromResume.jobId)
      setSelectedResumeId(state.fromResume.resumeId)
    }
    if (state?.questionSetId) {
      setSelectedQuestionSetId(state.questionSetId)
    }
  }, [location.state])

  useEffect(() => {
    if (!selectedResumeId && resumesQuery.data?.length) setSelectedResumeId(resumesQuery.data[0].id)
  }, [resumesQuery.data, selectedResumeId])

  useEffect(() => {
    if (!selectedJobId && jobsQuery.data?.length) setSelectedJobId(jobsQuery.data[0].id)
  }, [jobsQuery.data, selectedJobId])

  useEffect(() => {
    if (!selectedQuestionSetId && questionSetsQuery.data?.length) {
      setSelectedQuestionSetId(questionSetsQuery.data[0].id)
    }
  }, [questionSetsQuery.data, selectedQuestionSetId])

  const startCoachMutation = useMutation({
    mutationFn: () => {
      const resumeId = selectedResumeId
      const jobId = selectedJobId
      if (!resumeId || !jobId) {
        throw new Error('请先选择简历和岗位')
      }
      return interviewApi.coachStart({ jd_id: jobId, resume_id: resumeId })
    },
    onSuccess: (data) => {
      setCoachSessionId(data.session_id)
      setCoachMessages([
        { role: 'ai', message: data.opening_message },
        { role: 'ai', message: data.first_question },
      ])
      setCoachReport(null)
      setCoachFeedback(null)
      setInFollowup(false)
      setCoachActive(true)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const startCoachFromSetMutation = useMutation({
    mutationFn: (questionSetId: number) => interviewApi.startCoachFromQuestionSet(questionSetId),
    onSuccess: (data) => {
      setCoachSessionId(data.session_id)
      setCoachMessages([
        { role: 'ai', message: data.opening_message },
        { role: 'ai', message: data.first_question },
      ])
      setCoachReport(null)
      setCoachFeedback(null)
      setInFollowup(false)
      setCoachActive(true)
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const submitAnswerMutation = useMutation({
    mutationFn: ({ sessionId, answer }: { sessionId: number; answer: string }) =>
      interviewApi.coachAnswer({ session_id: sessionId, answer }),
    onSuccess: (data) => {
      const immediateScoreFeedback = formatImmediateScoreFeedback(data.score, data.feedback)
      setCoachMessages((prev) => [
        ...prev,
        { role: 'user', message: coachAnswer },
        { role: 'ai', message: immediateScoreFeedback, score: data.score },
      ])
      setCoachFeedback(immediateScoreFeedback)
      setCoachAnswer('')
      if (data.next_question) {
        setCoachMessages((prev) => [...prev, { role: 'ai', message: data.next_question! }])
      } else {
        setInFollowup(true)
      }
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const endCoachMutation = useMutation({
    mutationFn: ({ sessionId, followupSkipped }: { sessionId: number; followupSkipped: boolean }) =>
      interviewApi.coachEnd(sessionId, followupSkipped),
    onSuccess: (data) => {
      setCoachReport({ review_report: data.review_report, average_score: data.average_score })
      setCoachActive(false)
      setFeedback('面试已结束，复盘报告已生成。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  // First screen structure: left = question set + preview, right = coach entry
  // Second screen: left = last training result, right = history entry

  const currentQuestionSet =
    questionSetsQuery.data?.find((questionSet) => questionSet.id === selectedQuestionSetId) ??
    questionSetsQuery.data?.[0] ??
    null
  const activeReport = coachReport ?? latestReportQuery.data ?? null
  const activeReportAverageScore = coachReport?.average_score ?? latestReportQuery.data?.average_score ?? null
  const activeReportDuration = latestCompletedSession?.duration ?? null

  return (
    <WorkspaceShell
      title="面试工作区"
      subtitle="生成面试题目，进行 AI 对练"
      statusRail={feedback ? (
        <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
          {feedback}
        </div>
      ) : null}
    >
      <div className="flex flex-col gap-8">
        {/* 第一屏：左侧题集卡+题目预览，右侧教练入口卡 */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* 左侧：当前题集卡 */}
          <ResultFrame
            status={currentQuestionSet ? 'success' : 'loading'}
            title="当前题集"
            summary="当前训练材料决定你接下来练什么题，先确认题集，再进入面试教练。"
            headerMeta={
              currentQuestionSet ? (
                <div className="rounded-full bg-[var(--color-surface)] px-3 py-1 text-xs font-medium text-[var(--color-ink)]">
                  {currentQuestionSet.questions.length} 道题
                </div>
              ) : null
            }
            notice={!currentQuestionSet ? '暂无题集，请先生成题目。' : undefined}
          >
            {currentQuestionSet ? (
              <>
                <div className="rounded-xl bg-[var(--color-surface)] p-4">
                  <p className="text-sm font-medium text-[var(--color-ink)]">{currentQuestionSet.title}</p>
                  <p className="mt-1 text-xs text-[var(--color-muted)]">
                    题集已准备完成，可直接进入训练。
                  </p>
                </div>
                <div className="max-h-32 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-4">
                  <p className="text-xs leading-6 text-[var(--color-ink-tertiary)] line-clamp-4">
                    {currentQuestionSet.questions.slice(0, 2).map((q, i) => (
                      <span key={i}>Q{i + 1}: {q.question_text.slice(0, 50)}... {'\n'}</span>
                    ))}
                    {currentQuestionSet.questions.length > 2 && `...等 ${currentQuestionSet.questions.length} 道题`}
                  </p>
                </div>
              </>
            ) : (
              <div className="rounded-xl bg-[var(--color-surface)] p-4 text-sm text-[var(--color-muted)]">
                当前还没有可练习的题集。
              </div>
            )}
          </ResultFrame>

          {/* 右侧：教练入口卡 */}
          <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <span className="text-xl">🎯</span>
              <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">面试教练</h3>
            </div>
            <div className="space-y-3">
              <FormField label="简历">
                <Select value={selectedResumeId ?? ''} onChange={(event) => setSelectedResumeId(Number(event.target.value))}>
                  {resumesQuery.data?.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="目标岗位">
                <Select value={selectedJobId ?? ''} onChange={(event) => setSelectedJobId(Number(event.target.value))}>
                  {jobsQuery.data?.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} @ {job.company}
                    </option>
                  ))}
                </Select>
              </FormField>
              <PrimaryButton
                type="button"
                onClick={() => {
                  if (selectedQuestionSetId) {
                    startCoachFromSetMutation.mutate(selectedQuestionSetId)
                    return
                  }
                  startCoachMutation.mutate()
                }}
                disabled={
                  startCoachMutation.isPending ||
                  startCoachFromSetMutation.isPending ||
                  (!selectedQuestionSetId && (!selectedResumeId || !selectedJobId))
                }
                className="w-full"
              >
                {startCoachMutation.isPending || startCoachFromSetMutation.isPending ? '启动中...' : '开始练习'}
              </PrimaryButton>
            </div>
          </div>
        </div>

        {/* 第二屏：左侧最近训练结果摘要卡，右侧历史训练入口 */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* 左侧：最近训练结果摘要卡 */}
          <ResultFrame
            status={activeReport ? 'success' : 'loading'}
            title="最近训练结果"
            summary="最近一次训练结果保留为主结果，方便你快速判断是否继续练习或回看历史。"
            headerMeta={
              activeReportAverageScore != null ? (
                <div className="rounded-full bg-[var(--color-surface)] px-3 py-1 text-xs font-medium text-[var(--color-ink)]">
                  平均 {activeReportAverageScore} 分
                </div>
              ) : null
            }
            notice={!activeReport ? '暂无训练记录，请开始练习。' : undefined}
            actions={
              activeReport ? (
                <SecondaryButton type="button" onClick={() => { setCoachReport(null); setCoachMessages([]) }}>
                  重新开始
                </SecondaryButton>
              ) : undefined
            }
          >
            {activeReport ? (
              <>
                <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-4">
                  <span className="text-sm text-[var(--color-ink)]">平均得分</span>
                  <span className="text-lg font-bold text-[var(--color-accent)]">{activeReportAverageScore}分</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-4">
                  <span className="text-sm text-[var(--color-ink)]">练习时间</span>
                  <span className="text-sm font-medium text-[var(--color-ink)]">
                    {activeReportDuration ? `${activeReportDuration} 分钟` : `约 ${Math.max(coachMessages.length * 2, 2)} 分钟`}
                  </span>
                </div>
                <div className="rounded-xl bg-[var(--color-surface)] p-4">
                  <p className="text-xs text-[var(--color-muted)]">简短反馈</p>
                  <p className="text-sm text-[var(--color-ink)] line-clamp-2">
                    {activeReport.review_report.overall_comment || '继续加油练习！'}
                  </p>
                </div>
              </>
            ) : (
              <div className="rounded-xl bg-[var(--color-surface)] p-4 text-sm text-[var(--color-muted)]">
                当前还没有训练结果。
              </div>
            )}
          </ResultFrame>

          {/* 右侧：历史训练入口 */}
          <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <span className="text-xl">📚</span>
              <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">历史题集</h3>
            </div>
            <div className="space-y-3">
              {questionSetsQuery.data && questionSetsQuery.data.length > 0 ? (
                <div className="space-y-2">
                  {questionSetsQuery.data.slice(0, 3).map((qs: InterviewQuestionSet) => (
                    <button
                      key={qs.id}
                      onClick={() => setSelectedQuestionSetId(qs.id)}
                      className={`flex w-full items-center justify-between rounded-xl border bg-white px-3 py-2 text-left transition-colors hover:border-[var(--color-accent)]/30 ${
                        selectedQuestionSetId === qs.id
                          ? 'border-[var(--color-accent)]/40 bg-[var(--color-surface)]'
                          : 'border-[var(--color-border)]'
                      }`}
                    >
                      <span className="text-sm text-[var(--color-ink)] truncate">{qs.title}</span>
                      <span className="text-xs text-[var(--color-muted)]">{qs.questions.length}题</span>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-[var(--color-muted)]">暂无历史题集</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Active coach view */}
      {coachActive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-[var(--color-ink)]">面试练习中</h3>
              <PrimaryButton type="button" onClick={() => endCoachMutation.mutate({ sessionId: coachSessionId!, followupSkipped: inFollowup })}>
                结束面试
              </PrimaryButton>
            </div>
            <div className="flex max-h-96 flex-col gap-2 overflow-y-auto">
              {coachMessages.map((msg, i) => (
                <ChatBubble key={i} role={msg.role} message={msg.message} score={msg.score} />
              ))}
            </div>
            {coachFeedback && (
              <div className="rounded-xl bg-[var(--color-surface-sunken)] px-4 py-2 text-sm">
                {coachFeedback}
              </div>
            )}
            <Textarea
              value={coachAnswer}
              onChange={(e) => setCoachAnswer(e.target.value)}
              placeholder="输入你的回答..."
              className="mt-4"
            />
            <div className="mt-4 flex gap-3">
              <PrimaryButton
                type="button"
                onClick={() => submitAnswerMutation.mutate({ sessionId: coachSessionId!, answer: coachAnswer })}
                disabled={!coachAnswer.trim()}
              >
                提交回答
              </PrimaryButton>
            </div>
          </div>
        </div>
      )}
    </WorkspaceShell>
  )
}
