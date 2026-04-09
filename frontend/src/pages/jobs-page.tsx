import type { ChangeEvent, KeyboardEvent } from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { AgentAssistantPanel } from '../components/agent/AgentAssistantPanel'
import { JobCard } from './components/JobCard'
import { jobsApi, readApiError, resumeApi } from '../lib/api'
import {
  EmptyHint,
  FormField,
  Input,
  PageHeader,
  PrimaryButton,
  ResultPanel,
  SectionCard,
  SecondaryButton,
  Textarea,
} from './page-primitives'

type JobFormState = {
  title: string
  company: string
  location: string
  description: string
  requirements: string
  sourceUrl: string
  source: string
}

type ImportStatus = {
  kind: 'success' | 'error'
  message: string
}

const initialJobForm: JobFormState = {
  title: '',
  company: '',
  location: '',
  description: '',
  requirements: '',
  sourceUrl: '',
  source: 'manual',
}

function deriveJobTitleFromFileName(fileName: string) {
  const baseName = fileName.replace(/\.[^.]+$/, '')
  const normalized = baseName.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim()
  return normalized || '导入岗位'
}

async function readFileText(file: File) {
  if ('text' in file) {
    return file.text()
  }
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      resolve(typeof reader.result === 'string' ? reader.result : '')
    }
    reader.onerror = () => {
      reject(reader.error ?? new Error('Failed to read file'))
    }
    reader.readAsText(file)
  })
}

function parseImportedJobFile(text: string, fileName: string): Partial<JobFormState> {
  const trimmedText = text.trim()
  const title = deriveJobTitleFromFileName(fileName)
  const fileExtension = fileName.split('.').pop()?.toLowerCase() ?? ''

  if (fileExtension === 'json') {
    try {
      const parsed = JSON.parse(trimmedText)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        const record = parsed as Record<string, unknown>
        return {
          title:
            typeof record.title === 'string' && record.title.trim() ? record.title.trim() : title,
          company:
            typeof record.company === 'string' && record.company.trim() ? record.company.trim() : '',
          location:
            typeof record.location === 'string' && record.location.trim() ? record.location.trim() : '',
          description:
            typeof record.description === 'string' && record.description.trim()
              ? record.description.trim()
              : trimmedText,
          requirements:
            typeof record.requirements === 'string' && record.requirements.trim()
              ? record.requirements.trim()
              : '',
          sourceUrl:
            typeof record.source_url === 'string' && record.source_url.trim()
              ? record.source_url.trim()
              : '',
          source: 'local_file',
        }
      }
    } catch {
      return { title, description: trimmedText, source: 'local_file' }
    }
  }
  return { title, description: trimmedText, source: 'local_file' }
}

export function JobsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [importStatus, setImportStatus] = useState<ImportStatus | null>(null)
  const [matchPreview, setMatchPreview] = useState<string | null>(null)
  const [jobForm, setJobForm] = useState<JobFormState>(initialJobForm)

  const selectedJob = useMemo(
    () => jobsQuery.data?.find((job) => job.id === selectedJobId) ?? null,
    [jobsQuery.data, selectedJobId],
  )

  useEffect(() => {
    if (!selectedJobId && jobsQuery.data?.length) {
      setSelectedJobId(jobsQuery.data[0].id)
    }
  }, [jobsQuery.data, selectedJobId])

  useEffect(() => {
    if (!selectedResumeId && resumesQuery.data?.length) {
      setSelectedResumeId(resumesQuery.data[0].id)
    }
  }, [resumesQuery.data, selectedResumeId])

  // Keyboard navigation: J/K to move up/down, Enter to view, Cmd+Enter to flow
  const handleKeyboardNav = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (!jobsQuery.data?.length) return

      const currentIndex = jobsQuery.data.findIndex((j) => j.id === selectedJobId)
      if (currentIndex === -1) return

      if (e.key === 'j' || e.key === 'J') {
        e.preventDefault()
        const nextIndex = Math.min(currentIndex + 1, jobsQuery.data.length - 1)
        setSelectedJobId(jobsQuery.data[nextIndex].id)
      } else if (e.key === 'k' || e.key === 'K') {
        e.preventDefault()
        const prevIndex = Math.max(currentIndex - 1, 0)
        setSelectedJobId(jobsQuery.data[prevIndex].id)
      } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        goToResumeOptimize()
      }
    },
    [jobsQuery.data, selectedJobId, navigate, selectedJob],
  )

  const goToResumeOptimize = useCallback(() => {
    if (!selectedJob) {
      setFeedback('请先选择一个岗位，再执行一键流转。')
      return
    }

    const payload = {
      jobId: selectedJob.id,
      title: selectedJob.title,
      company: selectedJob.company,
      location: selectedJob.location,
      description: selectedJob.description ?? '',
      requirements: selectedJob.requirements ?? '',
    }

    navigate(
      `/resume?fromJob=${selectedJob.id}&targetRole=${encodeURIComponent(`${selectedJob.title}（${selectedJob.company}）`)}`,
      { state: { fromJob: payload } },
    )
  }, [selectedJob, navigate])

  const createJobMutation = useMutation({
    mutationFn: jobsApi.create,
    onSuccess: async (job) => {
      await queryClient.invalidateQueries({ queryKey: ['jobs', 'list'] })
      setSelectedJobId(job.id)
      setFeedback('岗位创建成功。')
      setJobForm(initialJobForm)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const saveExternalJobMutation = useMutation({
    mutationFn: () =>
      jobsApi.saveExternal({
        title: jobForm.title,
        company: jobForm.company,
        location: jobForm.location,
        description: jobForm.description,
        requirements: jobForm.requirements || null,
        source_url: jobForm.sourceUrl || null,
      }),
    onSuccess: async (job) => {
      await queryClient.invalidateQueries({ queryKey: ['jobs', 'list'] })
      setSelectedJobId(job.id)
      setFeedback('岗位已收藏到岗位库。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const matchPreviewMutation = useMutation({
    mutationFn: () => jobsApi.previewMatch(selectedJobId!, { resume_id: selectedResumeId! }),
    onSuccess: (data) => {
      setMatchPreview(`Score ${data.score}\n\n${data.feedback}`)
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const persistMatchMutation = useMutation({
    mutationFn: () => jobsApi.persistMatch(selectedJobId!, { resume_id: selectedResumeId! }),
    onSuccess: async () => {
      setFeedback('匹配结果已保存。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const handleJobFileImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0]
    event.currentTarget.value = ''
    if (!file) return

    try {
      const text = await readFileText(file)
      const trimmedText = text.trim()
      if (!trimmedText) throw new Error('empty')

      const importedValues = parseImportedJobFile(text, file.name)
      setJobForm((current) => ({
        ...current,
        ...importedValues,
        title: importedValues.title?.trim() || deriveJobTitleFromFileName(file.name),
        description: importedValues.description?.trim() || trimmedText,
        source: importedValues.source ?? 'local_file',
      }))
      setImportStatus({
        kind: 'success',
        message: `已导入 ${file.name}，岗位标题和描述已填入表单。`,
      })
      setFeedback(null)
    } catch {
      setImportStatus({
        kind: 'error',
        message: '文件导入失败，请选择有效的 txt、md 或 json 文本文件。',
      })
    }
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 space-y-6 overflow-y-auto pr-6">
        <PageHeader
          eyebrow="岗位探索"
          title="探索公司岗位并分析匹配"
          description="导入或录入岗位后，可收藏岗位、匹配简历，并一键流转到简历优化。"
        />

        <div className="grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
          <SectionCard title="岗位探索与收藏" subtitle="先录入岗位信息，再执行收藏与匹配。">
            <div className="space-y-4">
              <FormField label="导入本地岗位文件" helper="支持 txt、md 和 json 文件。">
                <Input
                  type="file"
                  accept=".txt,.md,.json,text/plain,text/markdown,application/json"
                  onChange={handleJobFileImport}
                />
              </FormField>
              {importStatus ? (
                <div
                  className={
                    importStatus.kind === 'success'
                      ? 'rounded-[22px] bg-[rgba(86,128,99,0.12)] px-4 py-3 text-sm text-[var(--color-ink)]'
                      : 'rounded-[22px] bg-[rgba(199,107,79,0.12)] px-4 py-3 text-sm text-[var(--color-ink)]'
                  }
                >
                  {importStatus.message}
                </div>
              ) : null}
              <FormField label="岗位标题">
                <Input
                  value={jobForm.title}
                  onChange={(event) => setJobForm((value) => ({ ...value, title: event.target.value }))}
                />
              </FormField>
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="公司">
                  <Input
                    value={jobForm.company}
                    onChange={(event) =>
                      setJobForm((value) => ({ ...value, company: event.target.value }))
                    }
                  />
                </FormField>
                <FormField label="地点">
                  <Input
                    value={jobForm.location}
                    onChange={(event) =>
                      setJobForm((value) => ({ ...value, location: event.target.value }))
                    }
                  />
                </FormField>
              </div>
              <FormField label="招聘链接（可选）">
                <Input
                  value={jobForm.sourceUrl}
                  onChange={(event) => setJobForm((value) => ({ ...value, sourceUrl: event.target.value }))}
                  placeholder="https://company.com/careers/..."
                />
              </FormField>
              <FormField label="岗位描述">
                <Textarea
                  value={jobForm.description}
                  onChange={(event) =>
                    setJobForm((value) => ({ ...value, description: event.target.value }))
                  }
                />
              </FormField>
              <FormField label="岗位要求">
                <Textarea
                  value={jobForm.requirements}
                  onChange={(event) =>
                    setJobForm((value) => ({ ...value, requirements: event.target.value }))
                  }
                />
              </FormField>
              <div className="flex flex-wrap gap-3">
                <PrimaryButton
                  type="button"
                  onClick={() => createJobMutation.mutate(jobForm)}
                  disabled={
                    !jobForm.title.trim() ||
                    !jobForm.company.trim() ||
                    !jobForm.location.trim() ||
                    !jobForm.description.trim()
                  }
                >
                  创建岗位
                </PrimaryButton>
                <SecondaryButton
                  type="button"
                  onClick={() => saveExternalJobMutation.mutate()}
                  disabled={
                    !jobForm.title.trim() ||
                    !jobForm.company.trim() ||
                    !jobForm.location.trim() ||
                    !jobForm.description.trim()
                  }
                >
                  收藏到岗位库
                </SecondaryButton>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="匹配分析与流转"
            subtitle="选择岗位和简历，预览/保存匹配，并跳转简历优化。"
          >
            <div
              className="space-y-4"
              onKeyDown={handleKeyboardNav}
              tabIndex={0}
              role="region"
              aria-label="岗位卡片列表，使用 J/K 键导航，Enter 键选择，Cmd+Enter 键一键流转"
            >
              <div className="mb-4 flex items-center justify-between">
                <p className="text-xs text-[var(--color-muted)]">
                  {jobsQuery.data?.length ?? 0} 个岗位 | 按 J/K 导航 | ⌘+Enter 一键流转
                </p>
              </div>

              {jobsQuery.data && jobsQuery.data.length > 0 ? (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {jobsQuery.data.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      isSelected={job.id === selectedJobId}
                      onClick={() => setSelectedJobId(job.id)}
                      onDoubleClick={goToResumeOptimize}
                    />
                  ))}
                </div>
              ) : (
                <EmptyHint>暂无岗位，请先在左侧创建或导入岗位。</EmptyHint>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="简历">
                  <select
                    value={selectedResumeId ?? ''}
                    onChange={(event) => setSelectedResumeId(Number(event.target.value))}
                    className="w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]"
                  >
                    {resumesQuery.data?.map((resume) => (
                      <option key={resume.id} value={resume.id}>
                        #{resume.id} - {resume.title}
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>
              <div className="flex flex-wrap gap-3">
                <SecondaryButton
                  type="button"
                  onClick={() => matchPreviewMutation.mutate()}
                  disabled={!selectedJobId || !selectedResumeId}
                >
                  预览匹配结果
                </SecondaryButton>
                <PrimaryButton
                  type="button"
                  onClick={() => persistMatchMutation.mutate()}
                  disabled={!selectedJobId || !selectedResumeId}
                >
                  保存匹配结果
                </PrimaryButton>
                <PrimaryButton type="button" onClick={goToResumeOptimize} disabled={!selectedJobId}>
                  带着岗位去优化简历
                </PrimaryButton>
              </div>
              {feedback ? (
                <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
                  {feedback}
                </div>
              ) : null}
              {matchPreview ? (
                <ResultPanel label="匹配结果" content={matchPreview} />
              ) : (
                <EmptyHint>先预览或保存匹配结果，这里才会显示内容。</EmptyHint>
              )}
            </div>
          </SectionCard>
        </div>
      </div>

      <div className="w-[400px] flex-shrink-0">
        <AgentAssistantPanel
          page="job"
          resourceId={selectedJobId ?? undefined}
          quickActions={[
            { label: '🔍 搜索岗位', message: '帮我搜索公司招聘官网' },
            { label: '分析 JD', message: '请分析这个岗位的 JD 要求' },
            { label: '与简历匹配', message: '这个岗位和我的简历匹配吗？' },
          ]}
        />
      </div>
    </div>
  )
}
