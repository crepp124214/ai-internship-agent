// frontend/src/pages/jd-customize-page.tsx
import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { readApiError, jobsApi, resumeApi, type MatchReportData } from '../lib/api'
import {
  FormField,
  PageHeader,
  PrimaryButton,
  ResultPanel,
  SectionCard,
  SecondaryButton,
  Select,
  Textarea,
} from './page-primitives'
import { MatchReportCard } from './components/MatchReportCard'

export function JdCustomizePage() {
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [customInstructions, setCustomInstructions] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)
  const [customizedResume, setCustomizedResume] = useState<string | null>(null)
  const [matchReport, setMatchReport] = useState<MatchReportData | null>(null)

  const resumesQuery = useQuery({
    queryKey: ['resume', 'list'],
    queryFn: resumeApi.list,
  })

  const jobsQuery = useQuery({
    queryKey: ['jobs', 'list'],
    queryFn: jobsApi.list,
  })

  const customizeMutation = useMutation({
    mutationFn: () => {
      if (!selectedResumeId || !selectedJobId) throw new Error('请选择简历和岗位')
      return resumeApi.customizeForJd(
        selectedResumeId,
        selectedJobId,
        customInstructions || undefined,
      )
    },
    onSuccess: (data) => {
      setCustomizedResume(data.customized_resume)
      setMatchReport(data.match_report)
      setFeedback('简历定制完成！')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const effectiveResumeId = selectedResumeId ?? resumesQuery.data?.[0]?.id ?? null
  const effectiveJobId = selectedJobId ?? jobsQuery.data?.[0]?.id ?? null

  const selectedResume = resumesQuery.data?.find((r) => r.id === effectiveResumeId)
  const selectedJob = jobsQuery.data?.find((j) => j.id === effectiveJobId)

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="简历定制"
        title="JD 定制简历"
        description="选择简历和目标岗位，系统分析匹配度并生成针对该岗位优化的简历内容。"
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        {/* Left: Resume selection */}
        <SectionCard title="选择简历" subtitle="选择要定制的简历">
          <div className="space-y-4">
            <FormField label="简历">
              <Select
                value={effectiveResumeId ?? ''}
                onChange={(e) => setSelectedResumeId(Number(e.target.value))}
              >
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} - {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
            {selectedResume && (
              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-ink-muted)]">
                  简历预览
                </p>
                <p className="whitespace-pre-wrap text-sm leading-6 text-[var(--color-ink)]">
                  {selectedResume.processed_content ?? selectedResume.resume_text ?? '（无内容）'}
                </p>
              </div>
            )}
          </div>
        </SectionCard>

        {/* Right: Job selection */}
        <SectionCard title="选择目标岗位" subtitle="选择要申请的岗位">
          <div className="space-y-4">
            <FormField label="岗位">
              <Select
                value={effectiveJobId ?? ''}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
              >
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id} - {job.title} @ {job.company}
                  </option>
                ))}
              </Select>
            </FormField>
            {selectedJob && (
              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-ink-muted)]">
                  JD 预览
                </p>
                <p className="mb-2 text-sm font-medium text-[var(--color-ink)]">
                  {selectedJob.title} @ {selectedJob.company}
                </p>
                <p className="whitespace-pre-wrap text-sm leading-6 text-[var(--color-ink)]">
                  {selectedJob.description ?? '（无描述）'}
                </p>
              </div>
            )}
          </div>
        </SectionCard>
      </div>

      {/* Custom instructions */}
      <SectionCard title="定制指令（可选）" subtitle="告诉 AI 你希望突出或弱化哪些内容">
        <Textarea
          value={customInstructions}
          onChange={(e) => setCustomInstructions(e.target.value)}
          placeholder="例如：突出我的 Python 项目经验，淡化不相关的社团经历"
          className="min-h-20"
        />
      </SectionCard>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <PrimaryButton
          type="button"
          disabled={!effectiveResumeId || !effectiveJobId || customizeMutation.isPending}
          onClick={() => customizeMutation.mutate()}
        >
          {customizeMutation.isPending ? '定制中...' : '🚀 开始定制简历'}
        </PrimaryButton>
        {feedback && (
          <span className="text-sm text-[var(--color-ink)]">{feedback}</span>
        )}
        {customizedResume && (
          <SecondaryButton
            type="button"
            onClick={() => {
              navigator.clipboard.writeText(customizedResume)
              setFeedback('已复制到剪贴板')
            }}
          >
            📋 复制简历
          </SecondaryButton>
        )}
      </div>

      {/* Results */}
      {customizedResume && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <SectionCard title="定制后简历" subtitle="基于 JD 优化过的简历内容">
            <ResultPanel label="定制简历" content={customizedResume} />
          </SectionCard>
          {matchReport && (
            <SectionCard title="匹配报告" subtitle="简历与目标岗位的匹配度分析">
              <MatchReportCard report={matchReport} />
            </SectionCard>
          )}
        </div>
      )}
    </div>
  )
}
