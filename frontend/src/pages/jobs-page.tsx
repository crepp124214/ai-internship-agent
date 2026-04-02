import type { ChangeEvent } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

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
  Select,
  Textarea,
} from './page-primitives'

type JobFormState = {
  title: string
  company: string
  location: string
  description: string
  requirements: string
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
      reject(reader.error ?? new Error('无法读取文件'))
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
            typeof record.company === 'string' && record.company.trim()
              ? record.company.trim()
              : '',
          location:
            typeof record.location === 'string' && record.location.trim()
              ? record.location.trim()
              : '',
          description:
            typeof record.description === 'string' && record.description.trim()
              ? record.description.trim()
              : trimmedText,
          requirements:
            typeof record.requirements === 'string' && record.requirements.trim()
              ? record.requirements.trim()
              : '',
          source: 'local_file',
        }
      }
    } catch {
      return {
        title,
        description: trimmedText,
        source: 'local_file',
      }
    }
  }

  return {
    title,
    description: trimmedText,
    source: 'local_file',
  }
}

export function JobsPage() {
  const queryClient = useQueryClient()
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [importStatus, setImportStatus] = useState<ImportStatus | null>(null)
  const [matchPreview, setMatchPreview] = useState<string | null>(null)
  const [jobForm, setJobForm] = useState<JobFormState>(initialJobForm)

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

  const selectedJob = useMemo(
    () => jobsQuery.data?.find((job) => job.id === selectedJobId) ?? null,
    [jobsQuery.data, selectedJobId],
  )

  const matchHistoryQuery = useQuery({
    queryKey: ['jobs', 'match-history', selectedJobId],
    queryFn: () => jobsApi.getMatchHistory(selectedJobId!),
    enabled: Boolean(selectedJobId),
  })

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

  const matchPreviewMutation = useMutation({
    mutationFn: () => jobsApi.previewMatch(selectedJobId!, { resume_id: selectedResumeId! }),
    onSuccess: (data) => {
      setMatchPreview(`评分 ${data.score}\n\n${data.feedback}`)
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const persistMatchMutation = useMutation({
    mutationFn: () => jobsApi.persistMatch(selectedJobId!, { resume_id: selectedResumeId! }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['jobs', 'match-history', selectedJobId] })
      setMatchPreview(`评分 ${data.score}\n\n${data.feedback}`)
      setFeedback('岗位匹配结果已保存到历史记录。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const handleJobFileImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0]
    event.currentTarget.value = ''

    if (!file) {
      return
    }

    try {
      const text = await readFileText(file)
      const trimmedText = text.trim()

      if (!trimmedText) {
        throw new Error('empty')
      }

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
        message: `已导入 ${file.name}，标题和描述已回填到表单。`,
      })
      setFeedback(null)
    } catch {
      setImportStatus({
        kind: 'error',
        message: '文件读取失败，请选择有效的 txt、md 或 json 文本文件。',
      })
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="岗位匹配工作区"
        title="把目标岗位和当前简历放到同一张工作台上"
        description="在这里录入岗位、选择简历、预览匹配结果并保存历史，完成一条清晰的演示链路。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
        <SectionCard title="创建岗位" subtitle="先录入岗位信息，构建一套可复用的演示数据。">
          <div className="space-y-4">
            <FormField
              label="导入本地岗位文件"
              helper="支持 txt、md、json。上传后会自动读取文本，并尽量回填标题和描述。"
            >
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
            <FormField label="岗位名称">
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
              <FormField label="城市 / 地点">
                <Input
                  value={jobForm.location}
                  onChange={(event) =>
                    setJobForm((value) => ({ ...value, location: event.target.value }))
                  }
                />
              </FormField>
            </div>
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
          </div>
        </SectionCard>

        <SectionCard title="匹配操作" subtitle="选定岗位和简历后，先预览，再决定是否把结果保存到历史。">
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="岗位">
              <Select value={selectedJobId ?? ''} onChange={(event) => setSelectedJobId(Number(event.target.value))}>
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id} · {job.title}（{job.company}）
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="简历">
              <Select value={selectedResumeId ?? ''} onChange={(event) => setSelectedResumeId(Number(event.target.value))}>
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} · {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>

          {selectedJob ? (
            <div className="mt-4 rounded-[24px] border border-[var(--color-stroke)] bg-[var(--color-panel)] p-5">
              <p className="text-base font-semibold text-[var(--color-ink)]">{selectedJob.title}</p>
              <p className="mt-1 text-sm text-[var(--color-muted)]">
                {selectedJob.company} · {selectedJob.location}
              </p>
              <p className="mt-4 text-sm leading-7 text-[var(--color-ink)]">{selectedJob.description}</p>
            </div>
          ) : (
            <EmptyHint>请先创建岗位，再进行匹配。</EmptyHint>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton
              type="button"
              onClick={() => matchPreviewMutation.mutate()}
              disabled={!selectedJobId || !selectedResumeId}
            >
              预览匹配
            </SecondaryButton>
            <PrimaryButton
              type="button"
              onClick={() => persistMatchMutation.mutate()}
              disabled={!selectedJobId || !selectedResumeId}
            >
              保存匹配记录
            </PrimaryButton>
          </div>
          {feedback ? (
            <div className="mt-4 rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
              {feedback}
            </div>
          ) : null}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="当前匹配结果" subtitle="预览使用同一套后端能力，但不会写入历史记录。">
          {matchPreview ? (
            <ResultPanel label="匹配结果预览" content={matchPreview} />
          ) : (
            <EmptyHint>先预览或保存一次匹配结果，这里才会显示内容。</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="匹配历史" subtitle="保存过的结果会与当前岗位持续关联，方便回看。">
          <div className="space-y-4">
            {matchHistoryQuery.data?.length ? (
              matchHistoryQuery.data.map((item) => (
                <ResultPanel
                  key={item.id}
                  label={`匹配 #${item.id}`}
                  content={`评分 ${item.score}\n\n${item.feedback}`}
                  meta={item.created_at}
                />
              ))
            ) : (
              <EmptyHint>暂时还没有匹配历史。</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
