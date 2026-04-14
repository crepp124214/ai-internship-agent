// frontend/src/pages/resume-page.tsx
import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { jobsApi, readApiError, resumeApi, type MatchReportData } from '../lib/api'
import {
  FormField,
  Input,
  PrimaryButton,
  ResultFrame,
  ResultPanel,
  SectionCard,
  SecondaryButton,
  Select,
  Textarea,
  WorkspaceShell,
} from './page-primitives'
import { FloatingToolbar } from './components/FloatingToolbar'
import { ResumeDiffView } from './components/ResumeDiffView'

type JobFlowState = {
  fromJob?: {
    jobId: number
    title: string
    company: string
    location: string
    description: string
    requirements: string
  }
}

// Validate AI content - detect mock/prompt artifacts
function validateAiContent(content: string | null | undefined): boolean {
  if (!content || typeof content !== 'string') return false
  const trimmed = content.trim()
  if (!trimmed) return false

  // Check for prompt injection or mock markers
  const invalidPatterns = [
    /^mock-/i,
    /^prompt:/i,
    /^task:/i,
    /^agent/i,
    /\|.*\|/,
  ]

  for (const pattern of invalidPatterns) {
    if (pattern.test(trimmed)) return false
  }

  // Check if it's too short
  if (trimmed.length < 10) return false

  return true
}

export function ResumePage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [targetRole, setTargetRole] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)
  const [summaryPreview, setSummaryPreview] = useState<string | null>(null)
  const [improvementsPreview, setImprovementsPreview] = useState<string | null>(null)
  const [flowHint, setFlowHint] = useState<string | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [jdInstructions, setJdInstructions] = useState('')
  const [customizedResume, setCustomizedResume] = useState<string | null>(null)
  const [matchReport, setMatchReport] = useState<MatchReportData | null>(null)

  // Diff view state
  const [diffOriginal, setDiffOriginal] = useState<string>('')
  const [diffModified, setDiffModified] = useState<string>('')
  const [showDiff, setShowDiff] = useState(false)

  // Ref for resume content area (for FloatingToolbar)
  const resumeContentRef = useRef<HTMLDivElement>(null)

  const effectiveSelectedResumeId = selectedResumeId ?? resumesQuery.data?.[0]?.id ?? null
  const effectiveSelectedResume =
    resumesQuery.data?.find((resume) => resume.id === effectiveSelectedResumeId) ?? null

  const resumeText = effectiveSelectedResume?.processed_content ?? effectiveSelectedResume?.resume_text ?? ''

  useEffect(() => {
    const state = location.state as JobFlowState | null
    const flowTargetRole = searchParams.get('targetRole')
    const flowResumeId = searchParams.get('resume_id')

    if (flowTargetRole && !targetRole.trim()) {
      setTargetRole(flowTargetRole)
    }

    // Set selected resume from URL parameter
    if (flowResumeId) {
      const resumeIdNum = Number(flowResumeId)
      if (!isNaN(resumeIdNum) && resumesQuery.data?.some(r => r.id === resumeIdNum)) {
        setSelectedResumeId(resumeIdNum)
      }
    }

    if (state?.fromJob) {
      const fromJob = state.fromJob
      setFlowHint(`已从岗位探索带入：${fromJob.title} / ${fromJob.company}（${fromJob.location}）`)
      setSelectedJobId(fromJob.jobId)
      if (!targetRole.trim()) {
        setTargetRole(`${fromJob.title}（${fromJob.company}）`)
      }
      return
    }

    if (!flowTargetRole) {
      setFlowHint(null)
    }
  }, [location.state, searchParams, targetRole, resumesQuery.data])

  useEffect(() => {
    if (!selectedJobId && jobsQuery.data?.length) {
      setSelectedJobId(jobsQuery.data[0].id)
    }
  }, [jobsQuery.data, selectedJobId])

  const summaryPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewSummary(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => {
      // Validate AI response
      if (!validateAiContent(data.content)) {
        setFeedback('摘要生成服务返回了无效内容，请重试或稍后再试。')
        setSummaryPreview(null)
        return
      }
      setSummaryPreview(data.content)
      // Show diff view for summary
      setDiffOriginal(resumeText)
      setDiffModified(data.content)
      setShowDiff(true)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const summaryPersistMutation = useMutation({
    mutationFn: () => resumeApi.persistSummary(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: async () => {
      setSummaryPreview('摘要已保存。')
      setFeedback('摘要已保存到历史记录。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const improvementsPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewImprovements(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => {
      // Validate AI response
      if (!validateAiContent(data.content)) {
        setFeedback('优化建议生成服务返回了无效内容，请重试或稍后再试。')
        setImprovementsPreview(null)
        return
      }
      setImprovementsPreview(data.content)
      // Show diff view for improvements
      setDiffOriginal(resumeText)
      setDiffModified(data.content)
      setShowDiff(true)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const improvementsPersistMutation = useMutation({
    mutationFn: () => resumeApi.persistImprovements(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: async () => {
      setImprovementsPreview('优化建议已保存。')
      setFeedback('优化建议已保存到历史记录。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const customizeForJdMutation = useMutation({
    mutationFn: () => {
      if (!effectiveSelectedResumeId || !selectedJobId) {
        throw new Error('请先选择简历和目标岗位。')
      }
      return resumeApi.customizeForJd(effectiveSelectedResumeId, selectedJobId, jdInstructions || undefined)
    },
    onSuccess: (data) => {
      setCustomizedResume(data.customized_resume)
      setMatchReport(data.match_report)
      setFeedback('JD 定向优化完成。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  // Floating toolbar handlers
  const handleFloatingOptimize = (selectedText: string) => {
    setFeedback(`正在优化：${selectedText.slice(0, 50)}...`)
  }

  const handleFloatingSummarize = (selectedText: string) => {
    setFeedback(`正在摘要：${selectedText.slice(0, 50)}...`)
  }

  const handleFloatingExplain = (selectedText: string) => {
    setFeedback(`正在解释：${selectedText.slice(0, 50)}...`)
  }

  // Diff view handlers
  const handleDiffAccept = () => {
    if (improvementsPreview) {
      improvementsPersistMutation.mutate()
    } else if (summaryPreview) {
      summaryPersistMutation.mutate()
    }
    setShowDiff(false)
  }

  const handleDiffReject = () => {
    setShowDiff(false)
    setDiffOriginal('')
    setDiffModified('')
  }

  // Check if results exist
  const hasSummary = !!summaryPreview
  const hasImprovements = !!improvementsPreview
  const hasCustomized = !!customizedResume
  const hasMatchReport = !!matchReport

  return (
    <WorkspaceShell
      title="简历优化"
      subtitle="选择简历并进行 JD 定向优化。从已有简历中选择版本，结合目标岗位生成摘要与优化建议。"
      statusRail={feedback ? (
        <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
          {feedback}
        </div>
      ) : null}
    >
      <div className="flex flex-col gap-8">
        {/* 第一屏：当前简历 + 结果总览左右并列 */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* 左侧：当前简历卡 */}
          <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <span className="text-xl">📄</span>
              <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">当前简历</h3>
            </div>
            <div className="space-y-3">
              <FormField label="选择简历">
                <Select
                  value={selectedResumeId ?? ''}
                  onChange={(event) => setSelectedResumeId(Number(event.target.value))}
                >
                  {resumesQuery.data?.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title}
                    </option>
                  ))}
                </Select>
              </FormField>
              {effectiveSelectedResume && (
                <>
                  <div className="rounded-xl bg-[var(--color-surface)] p-4">
                    <p className="text-xs text-[var(--color-muted)]">更新时间</p>
                    <p className="text-sm text-[var(--color-ink)]">
                      {effectiveSelectedResume.updated_at
                        ? new Date(effectiveSelectedResume.updated_at).toLocaleDateString('zh-CN')
                        : '-'}
                    </p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-surface)] p-4">
                    <p className="text-xs text-[var(--color-muted)]">状态</p>
                    <p className="text-sm text-[var(--color-ink)]">
                      {effectiveSelectedResume.resume_text ? '有内容' : '空简历'}
                    </p>
                  </div>
                  <div
                    ref={resumeContentRef}
                    className="max-h-40 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-4"
                  >
                    <p className="whitespace-pre-wrap text-xs leading-6 text-[var(--color-ink-tertiary)] line-clamp-6">
                      {resumeText || '（简历内容为空）'}
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 右侧：结果总览卡 */}
          <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <span className="text-xl">📊</span>
              <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">结果总览</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-4">
                <span className="text-sm text-[var(--color-ink)]">简历摘要</span>
                <span className={`text-sm font-medium ${hasSummary ? 'text-green-600' : 'text-[var(--color-muted)]'}`}>
                  {hasSummary ? '✓ 已生成' : '○ 未生成'}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-4">
                <span className="text-sm text-[var(--color-ink)]">优化建议</span>
                <span className={`text-sm font-medium ${hasImprovements ? 'text-green-600' : 'text-[var(--color-muted)]'}`}>
                  {hasImprovements ? '✓ 已生成' : '○ 未生成'}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-4">
                <span className="text-sm text-[var(--color-ink)]">JD 定向优化</span>
                <span className={`text-sm font-medium ${hasCustomized ? 'text-green-600' : 'text-[var(--color-muted)]'}`}>
                  {hasCustomized ? '✓ 已生成' : '○ 未生成'}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-4">
                <span className="text-sm text-[var(--color-ink)]">匹配报告</span>
                <span className={`text-sm font-medium ${hasMatchReport ? 'text-green-600' : 'text-[var(--color-muted)]'}`}>
                  {hasMatchReport ? '✓ 已生成' : '○ 未生成'}
                </span>
              </div>
              {flowHint && (
                <div className="rounded-xl bg-[rgba(86,128,99,0.12)] px-3 py-2 text-xs text-[var(--color-ink)]">
                  {flowHint}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 第二屏：结果操作区 */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">操作</h3>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="目标岗位（可选）">
              <Input
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder="例如：后端开发实习生"
              />
            </FormField>
            <FormField label="目标 JD 岗位">
              <Select
                value={selectedJobId ?? ''}
                onChange={(event) => setSelectedJobId(Number(event.target.value))}
              >
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title} @ {job.company}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="JD 优化指令（可选）" helper="例如：突出 Python + FastAPI 项目经历">
              <Textarea
                value={jdInstructions}
                onChange={(event) => setJdInstructions(event.target.value)}
                placeholder="例如：突出 Python + FastAPI 项目经历"
                className="min-h-20"
              />
            </FormField>
            <div className="flex flex-wrap gap-3 md:col-span-2">
              <SecondaryButton
                type="button"
                onClick={() => summaryPreviewMutation.mutate()}
                disabled={!effectiveSelectedResumeId || !resumeText || summaryPreviewMutation.isPending}
              >
                {summaryPreviewMutation.isPending ? '生成中...' : '预览摘要'}
              </SecondaryButton>
              <SecondaryButton
                type="button"
                onClick={() => improvementsPreviewMutation.mutate()}
                disabled={!effectiveSelectedResumeId || !resumeText || improvementsPreviewMutation.isPending}
              >
                {improvementsPreviewMutation.isPending ? '生成中...' : '预览优化建议'}
              </SecondaryButton>
              <PrimaryButton
                type="button"
                onClick={() => customizeForJdMutation.mutate()}
                disabled={!effectiveSelectedResumeId || !selectedJobId || customizeForJdMutation.isPending}
              >
                {customizeForJdMutation.isPending ? '优化中...' : 'JD 定向优化'}
              </PrimaryButton>
              {customizedResume && (
                <PrimaryButton
                  type="button"
                  onClick={() => {
                    navigate(
                      `/interview?jobId=${selectedJobId}&resumeId=${effectiveSelectedResumeId}`,
                      { state: { fromResume: { jobId: selectedJobId, resumeId: effectiveSelectedResumeId } } },
                    )
                  }}
                >
                  进入面试准备
                </PrimaryButton>
              )}
            </div>
          </div>
        </div>

        {/* Floating Toolbar */}
        <FloatingToolbar
          targetRef={resumeContentRef}
          onOptimize={handleFloatingOptimize}
          onSummarize={handleFloatingSummarize}
          onExplain={handleFloatingExplain}
        />

        {/* Diff 视图 */}
        {showDiff && diffOriginal && diffModified && (
          <SectionCard title="AI 修改建议" subtitle="查看并决定是否接受 AI 的修改。">
            <ResumeDiffView
              original={diffOriginal}
              modified={diffModified}
              onAccept={handleDiffAccept}
              onReject={handleDiffReject}
              loading={summaryPreviewMutation.isPending || improvementsPreviewMutation.isPending}
            />
          </SectionCard>
        )}

        {/* 结果查看区 - 默认主视觉：优化建议 */}
        {(summaryPreview || improvementsPreview || customizedResume || matchReport) && !showDiff && (
          <ResultFrame
            status={customizedResume ? 'success' : hasImprovements ? 'success' : 'loading'}
            title="简历优化结果"
            summary="主结果默认聚焦优化建议，其余结果保留为次级工作面板，便于继续推进下一步。"
            headerMeta={
              <div className="rounded-full bg-[var(--color-surface)] px-3 py-1 text-xs font-medium text-[var(--color-ink)]">
                已生成 {Number(hasSummary) + Number(hasImprovements) + Number(hasCustomized) + Number(hasMatchReport)} / 4 项结果
              </div>
            }
            notice={
              customizeForJdMutation.isPending
                ? '正在生成 JD 定向优化...'
                : summaryPreviewMutation.isPending
                  ? '正在生成摘要...'
                  : improvementsPreviewMutation.isPending
                    ? '正在生成优化建议...'
                    : undefined
            }
          >
            <div className="grid gap-6 xl:grid-cols-2">
              <ResultPanel
                label="优化建议"
                content={improvementsPreview ?? '点击上方「预览优化建议」'}
              />
              <ResultPanel
                label="简历摘要"
                content={summaryPreview ?? '点击上方「预览摘要」'}
              />
              <ResultPanel
                label="JD 定向优化"
                content={customizedResume ?? '点击上方「JD 定向优化」'}
              />
              <ResultPanel
                label="匹配报告"
                content={matchReport ? '已完成匹配分析' : '完成定向优化后显示报告'}
              />
            </div>
          </ResultFrame>
        )}
      </div>
    </WorkspaceShell>
  )
}
