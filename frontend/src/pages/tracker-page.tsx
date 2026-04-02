import { useEffect, useState, type ChangeEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { jobsApi, readApiError, resumeApi, trackerApi } from '../lib/api'
import {
  EmptyHint,
  FormField,
  Input,
  PageHeader,
  PrimaryButton,
  ResultPanel,
  SectionCard,
  SecondaryButton,
  Select,
  Textarea,
} from './page-primitives'

const defaultStatuses = [
  { value: 'applied', label: '已投递' },
  { value: 'screening', label: '筛选中' },
  { value: 'interview', label: '面试中' },
  { value: 'offer', label: '已发 Offer' },
  { value: 'rejected', label: '未通过' },
]

type TrackerImportDraft = Partial<{
  job_id: string
  resume_id: string
  status: string
  notes: string
}>

function formatAdviceContent(summary: string, nextSteps: string[], risks: string[]) {
  const nextStepsText = nextSteps.length ? nextSteps.map((step) => `- ${step}`).join('\n') : '- 暂无'
  const risksText = risks.length ? risks.map((risk) => `- ${risk}`).join('\n') : '- 暂无'

  return `${summary}\n\n下一步\n${nextStepsText}\n\n风险\n${risksText}`
}

function isKnownStatus(status: string | undefined) {
  return Boolean(status) && defaultStatuses.some((item) => item.value === status)
}

function parseTrackerImportText(content: string): TrackerImportDraft {
  const draft: TrackerImportDraft = {}

  const jobMatch = content.match(/(?:^|\n)\s*job[_\s-]?id\s*[:=]\s*(\d+)/i)
  const resumeMatch = content.match(/(?:^|\n)\s*resume[_\s-]?id\s*[:=]\s*(\d+)/i)
  const statusMatch = content.match(/(?:^|\n)\s*status\s*[:=]\s*([a-z_]+)/i)
  const notesMatch = content.match(/(?:^|\n)\s*notes?\s*[:=]\s*([\s\S]*)$/i)

  if (jobMatch?.[1]) {
    draft.job_id = jobMatch[1]
  }

  if (resumeMatch?.[1]) {
    draft.resume_id = resumeMatch[1]
  }

  if (statusMatch?.[1] && isKnownStatus(statusMatch[1].toLowerCase())) {
    draft.status = statusMatch[1].toLowerCase()
  }

  const notes = notesMatch?.[1]?.trim() || content.trim()
  if (notes) {
    draft.notes = notes
  }

  return draft
}

function parseTrackerImportJson(content: string): TrackerImportDraft {
  const parsed = JSON.parse(content) as Record<string, unknown>
  const source =
    parsed.application && typeof parsed.application === 'object'
      ? (parsed.application as Record<string, unknown>)
      : parsed.tracker && typeof parsed.tracker === 'object'
        ? (parsed.tracker as Record<string, unknown>)
        : parsed

  const draft: TrackerImportDraft = {}

  const jobId = source.job_id ?? source.jobId
  const resumeId = source.resume_id ?? source.resumeId
  const status = source.status
  const notes = source.notes ?? source.comment ?? source.memo

  if (jobId !== undefined && jobId !== null && String(jobId).trim()) {
    draft.job_id = String(jobId)
  }

  if (resumeId !== undefined && resumeId !== null && String(resumeId).trim()) {
    draft.resume_id = String(resumeId)
  }

  if (typeof status === 'string' && isKnownStatus(status.trim().toLowerCase())) {
    draft.status = status.trim().toLowerCase()
  }

  if (typeof notes === 'string' && notes.trim()) {
    draft.notes = notes.trim()
  }

  return draft
}

function parseTrackerImportContent(fileName: string, content: string): TrackerImportDraft {
  if (fileName.toLowerCase().endsWith('.json')) {
    return parseTrackerImportJson(content)
  }

  const trimmed = content.trim()
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      return parseTrackerImportJson(content)
    } catch {
      return parseTrackerImportText(content)
    }
  }

  return parseTrackerImportText(content)
}

export function TrackerPage() {
  const queryClient = useQueryClient()
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const applicationsQuery = useQuery({ queryKey: ['tracker', 'applications'], queryFn: trackerApi.listApplications })

  const [selectedApplicationId, setSelectedApplicationId] = useState<number | null>(null)
  const [advicePreview, setAdvicePreview] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [importFeedback, setImportFeedback] = useState<string | null>(null)
  const [applicationForm, setApplicationForm] = useState({
    job_id: '',
    resume_id: '',
    status: 'applied',
    notes: '',
  })

  useEffect(() => {
    if (!selectedApplicationId && applicationsQuery.data?.length) {
      setSelectedApplicationId(applicationsQuery.data[0].id)
    }
  }, [applicationsQuery.data, selectedApplicationId])

  const adviceHistoryQuery = useQuery({
    queryKey: ['tracker', 'advice-history', selectedApplicationId],
    queryFn: () => trackerApi.getAdviceHistory(selectedApplicationId!),
    enabled: Boolean(selectedApplicationId),
  })

  const applyImportedDraft = (draft: TrackerImportDraft) => {
    setApplicationForm((current) => ({
      job_id: draft.job_id ?? current.job_id,
      resume_id: draft.resume_id ?? current.resume_id,
      status: draft.status && isKnownStatus(draft.status) ? draft.status : current.status,
      notes: draft.notes ?? current.notes,
    }))
  }

  const handleImportFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }

    try {
      const content = await file.text()
      const draft = parseTrackerImportContent(file.name, content)
      applyImportedDraft(draft)
      setImportFeedback(`已导入 ${file.name}，表单已回填。`)
    } catch (error) {
      setImportFeedback(readApiError(error))
    } finally {
      event.target.value = ''
    }
  }

  const createApplicationMutation = useMutation({
    mutationFn: () =>
      trackerApi.createApplication({
        job_id: Number(applicationForm.job_id),
        resume_id: Number(applicationForm.resume_id),
        status: applicationForm.status,
        notes: applicationForm.notes || null,
      }),
    onSuccess: async (application) => {
      await queryClient.invalidateQueries({ queryKey: ['tracker', 'applications'] })
      setSelectedApplicationId(application.id)
      setFeedback('投递记录已创建，接下来可以预览对应的 AI 建议。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const previewAdviceMutation = useMutation({
    mutationFn: () => trackerApi.previewAdvice(selectedApplicationId!),
    onSuccess: (data) => {
      setAdvicePreview(formatAdviceContent(data.summary, data.next_steps, data.risks))
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const persistAdviceMutation = useMutation({
    mutationFn: () => trackerApi.persistAdvice(selectedApplicationId!),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['tracker', 'advice-history', selectedApplicationId] })
      setAdvicePreview(formatAdviceContent(data.summary, data.next_steps, data.risks))
      setFeedback('投递建议已保存到历史记录。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="投递追踪工作区"
        title="把投递状态、AI 建议和历史记录放到同一处"
        description="围绕岗位、简历和投递状态，整理一条可演示的投递链路。你可以先创建投递，再预览建议，最后把建议沉淀为历史记录。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard title="导入投递说明" subtitle="支持本地 txt / md / json，直接回填当前投递表单。">
          <div className="space-y-4">
            <FormField label="本地说明文件" helper="JSON 会回填岗位、简历、状态和备注；文本会回填备注，并尝试解析简单字段。">
              <Input type="file" accept=".txt,.md,.json" onChange={handleImportFile} />
            </FormField>
            {importFeedback ? (
              <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
                {importFeedback}
              </div>
            ) : (
              <EmptyHint>上传一份本地投递说明，就能把常用字段先填好，减少重复录入。</EmptyHint>
            )}
          </div>
        </SectionCard>

        <SectionCard title="创建投递" subtitle="把岗位与简历绑定成一条可追踪的投递记录。">
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="岗位">
              <Select
                value={applicationForm.job_id}
                onChange={(event) => setApplicationForm((value) => ({ ...value, job_id: event.target.value }))}
              >
                <option value="">请选择岗位</option>
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id} · {job.title}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="简历">
              <Select
                value={applicationForm.resume_id}
                onChange={(event) => setApplicationForm((value) => ({ ...value, resume_id: event.target.value }))}
              >
                <option value="">请选择简历</option>
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} · {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-[0.42fr_0.58fr]">
            <FormField label="当前阶段">
              <Select
                value={applicationForm.status}
                onChange={(event) => setApplicationForm((value) => ({ ...value, status: event.target.value }))}
              >
                {defaultStatuses.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="备注">
              <Textarea
                value={applicationForm.notes}
                onChange={(event) => setApplicationForm((value) => ({ ...value, notes: event.target.value }))}
                placeholder="例如：已完成一轮电话面试，等待 HR 反馈。"
              />
            </FormField>
          </div>
          <div className="mt-4">
            <PrimaryButton
              type="button"
              onClick={() => createApplicationMutation.mutate()}
              disabled={!applicationForm.job_id || !applicationForm.resume_id}
            >
              创建投递记录
            </PrimaryButton>
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="建议操作" subtitle="先看 AI 预览，再决定是否保存为历史建议。">
          <div className="grid gap-4 md:grid-cols-[0.48fr_0.52fr]">
            <FormField label="当前投递">
              <Select
                value={selectedApplicationId ?? ''}
                onChange={(event) => setSelectedApplicationId(Number(event.target.value))}
              >
                <option value="">请选择投递</option>
                {applicationsQuery.data?.map((application) => {
                  const statusLabel =
                    defaultStatuses.find((item) => item.value === application.status)?.label ?? application.status

                  return (
                    <option key={application.id} value={application.id}>
                      #{application.id} · 岗位 {application.job_id} · {statusLabel}
                    </option>
                  )
                })}
              </Select>
            </FormField>
            <div className="flex flex-wrap items-end gap-3">
              <SecondaryButton type="button" onClick={() => previewAdviceMutation.mutate()} disabled={!selectedApplicationId}>
                预览建议
              </SecondaryButton>
              <PrimaryButton type="button" onClick={() => persistAdviceMutation.mutate()} disabled={!selectedApplicationId}>
                保存建议
              </PrimaryButton>
            </div>
          </div>

          {feedback ? (
            <div className="mt-4 rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
              {feedback}
            </div>
          ) : null}

          <div className="mt-4">
            {advicePreview ? (
              <ResultPanel label="建议预览" content={advicePreview} />
            ) : (
              <EmptyHint>先选择一条投递记录，再生成对应建议。</EmptyHint>
            )}
          </div>
        </SectionCard>

        <SectionCard title="投递记录" subtitle="按时间查看每条投递的岗位、简历、状态与备注。">
          <div className="space-y-4">
            {applicationsQuery.data?.length ? (
              applicationsQuery.data.map((application) => (
                <ResultPanel
                  key={application.id}
                  label={`投递 #${application.id}`}
                  content={`岗位：${application.job_id}\n简历：${application.resume_id}\n阶段：${
                    defaultStatuses.find((status) => status.value === application.status)?.label ?? application.status
                  }\n备注：${application.notes ?? '暂无备注'}`}
                  meta={application.application_date}
                />
              ))
            ) : (
              <EmptyHint>暂时还没有投递记录。先创建一条投递，马上就能开始追踪它的状态变化。</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="建议历史" subtitle="已经保存过的投递建议会持续留在这里，方便回看与复用。">
        <div className="space-y-4">
          {adviceHistoryQuery.data?.length ? (
            adviceHistoryQuery.data.map((item) => (
              <ResultPanel
                key={item.id}
                label={`建议 #${item.id}`}
                content={formatAdviceContent(item.summary, item.next_steps, item.risks)}
                meta={item.created_at}
              />
            ))
          ) : (
            <EmptyHint>暂时还没有建议历史。先在右侧保存一次建议，这里就会出现可追溯记录。</EmptyHint>
          )}
        </div>
      </SectionCard>
    </div>
  )
}
