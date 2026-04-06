import { useState, type ChangeEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { readApiError, resumeApi, type Resume } from '../lib/api'
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

function getFileExtension(fileName: string) {
  const lastDotIndex = fileName.lastIndexOf('.')

  if (lastDotIndex < 0) {
    return ''
  }

  return fileName.slice(lastDotIndex + 1).toLowerCase()
}

function stripFileExtension(fileName: string) {
  const lastDotIndex = fileName.lastIndexOf('.')

  if (lastDotIndex < 0) {
    return fileName
  }

  return fileName.slice(0, lastDotIndex)
}

function sanitizeFileName(fileName: string) {
  return fileName.replace(/[^a-zA-Z0-9._-]+/g, '-')
}

function resolveResumeTitle(manualTitle: string, file: File) {
  const trimmedTitle = manualTitle.trim()

  if (trimmedTitle) {
    return trimmedTitle
  }

  const strippedFileName = stripFileExtension(file.name).trim()
  return strippedFileName || file.name
}

function isSupportedResumeImport(file: File) {
  const extension = getFileExtension(file.name)
  const mimeType = file.type.toLowerCase()

  return (
    ['txt', 'md', 'json'].includes(extension) ||
    mimeType.startsWith('text/') ||
    mimeType === 'application/json'
  )
}

function buildManualFilePath(title: string) {
  const safeTitle = sanitizeFileName(title.trim() || 'jianli')
  return `manual/${Date.now()}-${safeTitle}.txt`
}

function buildImportedFilePath(file: File) {
  return `imports/${Date.now()}-${sanitizeFileName(file.name)}`
}

async function readTextFile(file: File) {
  if (typeof file.text === 'function') {
    return file.text()
  }

  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error ?? new Error('Failed to read file'))
    reader.readAsText(file)
  })
}

export function ResumePage() {
  const queryClient = useQueryClient()
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [createTitle, setCreateTitle] = useState('')
  const [draftsByResumeId, setDraftsByResumeId] = useState<Record<number, { title: string; resumeText: string }>>({})
  const [targetRole, setTargetRole] = useState('')
  const [importStatus, setImportStatus] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [selectedImportFile, setSelectedImportFile] = useState<File | null>(null)
  const [importInputKey, setImportInputKey] = useState(0)
  const [summaryPreview, setSummaryPreview] = useState<string | null>(null)
  const [improvementsPreview, setImprovementsPreview] = useState<string | null>(null)

  const effectiveSelectedResumeId = selectedResumeId ?? resumesQuery.data?.[0]?.id ?? null
  const effectiveSelectedResume =
    resumesQuery.data?.find((resume) => resume.id === effectiveSelectedResumeId) ?? null

  const currentDraft = effectiveSelectedResumeId
    ? draftsByResumeId[effectiveSelectedResumeId] ??
      (effectiveSelectedResume
        ? {
            title: effectiveSelectedResume.title,
            resumeText: effectiveSelectedResume.processed_content ?? effectiveSelectedResume.resume_text ?? '',
          }
        : { title: '', resumeText: '' })
    : { title: '', resumeText: '' }

  const editTitle = currentDraft.title
  const resumeText = currentDraft.resumeText

  const updateCurrentDraft = (patch: Partial<{ title: string; resumeText: string }>) => {
    if (!effectiveSelectedResumeId) {
      return
    }

    setDraftsByResumeId((current) => ({
      ...current,
      [effectiveSelectedResumeId]: {
        title: patch.title ?? currentDraft.title,
        resumeText: patch.resumeText ?? currentDraft.resumeText,
      },
    }))
  }

  const summaryHistoryQuery = useQuery({
    queryKey: ['resume', 'summary-history', effectiveSelectedResumeId],
    queryFn: () => resumeApi.getSummaryHistory(effectiveSelectedResumeId!),
    enabled: Boolean(effectiveSelectedResumeId),
  })

  const optimizationHistoryQuery = useQuery({
    queryKey: ['resume', 'optimization-history', effectiveSelectedResumeId],
    queryFn: () => resumeApi.getOptimizationHistory(effectiveSelectedResumeId!),
    enabled: Boolean(effectiveSelectedResumeId),
  })

  const createResumeMutation = useMutation({
    mutationFn: ({ title, filePath }: { title: string; filePath: string }) =>
      resumeApi.create({
        title,
        file_path: filePath,
      }),
    onSuccess: async (resume) => {
      queryClient.setQueryData<Resume[]>(['resume', 'list'], (current = []) => [
        resume,
        ...current.filter((item) => item.id !== resume.id),
      ])
      await queryClient.invalidateQueries({ queryKey: ['resume', 'list'] })
      setSelectedResumeId(resume.id)
      setCreateTitle('')
      setFeedback('简历创建成功。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const updateResumeMutation = useMutation({
    mutationFn: (payload: { resume: Resume; title: string; resumeText: string }) =>
      resumeApi.update(payload.resume.id, {
        title: payload.title,
        resume_text: payload.resumeText,
        processed_content: payload.resumeText,
      }),
    onSuccess: async (resume) => {
      queryClient.setQueryData<Resume[]>(['resume', 'list'], (current = []) => [
        resume,
        ...current.filter((item) => item.id !== resume.id),
      ])
      await queryClient.invalidateQueries({ queryKey: ['resume', 'list'] })
      setSelectedResumeId(resume.id)
      setDraftsByResumeId((current) => ({
        ...current,
        [resume.id]: {
          title: resume.title,
          resumeText: resume.processed_content ?? resume.resume_text ?? '',
        },
      }))
      setFeedback('简历内容已更新。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const summaryPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewSummary(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => setSummaryPreview(data.content),
    onError: (error) => setFeedback(readApiError(error)),
  })

  const summaryPersistMutation = useMutation({
    mutationFn: () => resumeApi.persistSummary(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['resume', 'summary-history', effectiveSelectedResumeId] })
      setSummaryPreview(data.optimized_text)
      setFeedback('摘要已保存到历史记录。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const improvementsPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewImprovements(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => setImprovementsPreview(data.content),
    onError: (error) => setFeedback(readApiError(error)),
  })

  const improvementsPersistMutation = useMutation({
    mutationFn: () => resumeApi.persistImprovements(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['resume', 'optimization-history', effectiveSelectedResumeId] })
      setImprovementsPreview(data.optimized_text)
      setFeedback('优化建议已保存到历史记录。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const importResumeMutation = useMutation({
    mutationFn: async ({ file, title }: { file: File; title: string }) => {
      if (!isSupportedResumeImport(file)) {
        throw new Error('仅支持 txt、md 和 json 格式的简历文件。')
      }

      const resolvedTitle = resolveResumeTitle(title, file)

      setImportStatus(`正在读取 ${file.name}...`)
      const fileText = await readTextFile(file)

      setImportStatus(`正在创建 ${file.name}...`)
      const createdResume = await resumeApi.create({
        title: resolvedTitle,
        file_path: buildImportedFilePath(file),
      })

      setImportStatus(`正在把 ${file.name} 写回简历记录...`)
      const updatedResume = await resumeApi.update(createdResume.id, {
        title: resolvedTitle,
        resume_text: fileText,
        processed_content: fileText,
      })

      return {
        createdResume,
        updatedResume,
        resolvedTitle,
        fileText,
        fileName: file.name,
      }
    },
    onSuccess: async ({ updatedResume, resolvedTitle, fileText, fileName }) => {
      queryClient.setQueryData<Resume[]>(['resume', 'list'], (current = []) => [
        updatedResume,
        ...current.filter((item) => item.id !== updatedResume.id),
      ])
      await queryClient.invalidateQueries({ queryKey: ['resume', 'list'] })
      setSelectedResumeId(updatedResume.id)
      setDraftsByResumeId((current) => ({
        ...current,
        [updatedResume.id]: {
          title: updatedResume.title || resolvedTitle,
          resumeText: updatedResume.processed_content ?? updatedResume.resume_text ?? fileText,
        },
      }))
      setCreateTitle('')
      setSelectedImportFile(null)
      setImportStatus(`已导入 ${fileName}。`)
      setFeedback('简历已成功导入并保存。')
      setImportInputKey((value) => value + 1)
    },
    onError: (error) => {
      setImportStatus(null)
      setSelectedImportFile(null)
      setImportInputKey((value) => value + 1)
      setFeedback(readApiError(error))
    },
  })

  const handleImportFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0] ?? null

    setFeedback(null)
    setImportStatus(null)

    if (!file) {
      setSelectedImportFile(null)
      return
    }

    if (!isSupportedResumeImport(file)) {
      setSelectedImportFile(null)
      setFeedback('仅支持 txt、md 和 json 格式的简历文件。')
      setImportInputKey((value) => value + 1)
      return
    }

    setSelectedImportFile(file)
    setImportStatus(`已选择 ${file.name}。`)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="简历工作台"
        title="一次整理，持续追踪每次 AI 迭代"
        description="在同一页里维护简历内容、预览 AI 摘要与优化建议，并保留两类历史记录。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <SectionCard
          title="简历列表"
          subtitle="先整理出一份基础简历，再复用到岗位匹配、面试准备和投递追踪流程中。"
        >
          <div className="space-y-4">
            <FormField label="新建简历">
              <div className="flex flex-col gap-3 md:flex-row">
                <Input
                  value={createTitle}
                  onChange={(event) => setCreateTitle(event.target.value)}
                  placeholder="例如：暑期实习总简历"
                />
                <PrimaryButton
                  type="button"
                  disabled={!createTitle.trim() || createResumeMutation.isPending}
                  onClick={() =>
                    createResumeMutation.mutate({
                      title: createTitle.trim(),
                      filePath: buildManualFilePath(createTitle),
                    })
                  }
                >
                  创建
                </PrimaryButton>
              </div>
            </FormField>
            <FormField
              label="导入本地简历文本"
              helper="支持 txt、md 和 json。浏览器会先读取文件，再创建简历记录并写回内容。"
            >
              <div className="space-y-3">
                <input
                  key={importInputKey}
                  type="file"
                  accept=".txt,.md,.json,text/plain,application/json"
                  onChange={handleImportFileChange}
                  className="w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition file:mr-4 file:rounded-full file:border-0 file:bg-[var(--color-accent)] file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]"
                />
                {selectedImportFile ? (
                  <p className="text-sm text-[var(--color-ink)]">已选择：{selectedImportFile.name}</p>
                ) : (
                  <p className="text-sm text-[var(--color-muted)]">
                    选择一个本地文本文件，然后把它导入成新的简历记录。
                  </p>
                )}
                <PrimaryButton
                  type="button"
                  disabled={!selectedImportFile || importResumeMutation.isPending}
                  onClick={() => {
                    if (selectedImportFile) {
                      importResumeMutation.mutate({ file: selectedImportFile, title: createTitle })
                    }
                  }}
                >
                  {importResumeMutation.isPending ? '导入中...' : '导入并创建'}
                </PrimaryButton>
                {importStatus ? (
                  <p className="text-xs leading-5 text-[var(--color-muted)]">{importStatus}</p>
                ) : null}
              </div>
            </FormField>
            <FormField label="当前简历">
              <Select value={selectedResumeId ?? ''} onChange={(event) => setSelectedResumeId(Number(event.target.value))}>
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} - {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
            {feedback ? (
              <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
                {feedback}
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard
          title="简历内容"
          subtitle="这个页面会同时更新处理后内容和原始文本字段，保证演示链路稳定。"
        >
          {effectiveSelectedResume ? (
            <div className="space-y-4">
              <FormField label="标题">
                <Input value={editTitle} onChange={(event) => updateCurrentDraft({ title: event.target.value })} />
              </FormField>
              <FormField
                label="简历正文"
                helper="后端会优先读取处理后内容，必要时回退到原始文本。这个页面会同时更新两者。"
              >
                <Textarea
                  value={resumeText}
                  onChange={(event) => updateCurrentDraft({ resumeText: event.target.value })}
                  className="min-h-56"
                />
              </FormField>
              <FormField label="目标岗位">
                <Input
                  value={targetRole}
                  onChange={(event) => setTargetRole(event.target.value)}
                  placeholder="例如：后端开发实习生"
                />
              </FormField>
              <div className="flex flex-wrap gap-3">
                <PrimaryButton
                  type="button"
                  onClick={() =>
                    effectiveSelectedResume &&
                    updateResumeMutation.mutate({ resume: effectiveSelectedResume, title: editTitle, resumeText })
                  }
                >
                  保存简历
                </PrimaryButton>
                <SecondaryButton type="button" onClick={() => summaryPreviewMutation.mutate()} disabled={!effectiveSelectedResumeId}>
                  预览摘要
                </SecondaryButton>
                <SecondaryButton type="button" onClick={() => summaryPersistMutation.mutate()} disabled={!effectiveSelectedResumeId}>
                  保存摘要
                </SecondaryButton>
                <SecondaryButton type="button" onClick={() => improvementsPreviewMutation.mutate()} disabled={!effectiveSelectedResumeId}>
                  预览优化建议
                </SecondaryButton>
                <SecondaryButton type="button" onClick={() => improvementsPersistMutation.mutate()} disabled={!effectiveSelectedResumeId}>
                  保存优化建议
                </SecondaryButton>
              </div>
            </div>
          ) : (
            <EmptyHint>请先创建一份简历，再继续生成摘要、优化建议和下游匹配结果。</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="摘要" subtitle="预览不会写入历史，保存后才会生成可追踪记录。">
          {summaryPreview ? (
            <ResultPanel label="摘要预览" content={summaryPreview} />
          ) : (
            <EmptyHint>先执行预览或保存摘要，才能在这里看到最新生成内容。</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="优化建议" subtitle="这里会展示 AI 如何改写和增强这份简历。">
          {improvementsPreview ? (
            <ResultPanel label="优化建议预览" content={improvementsPreview} />
          ) : (
            <EmptyHint>先执行一次优化建议生成，这里才会出现可操作的改写内容。</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="摘要历史" subtitle="这里展示之前保存过的摘要记录。">
          <div className="space-y-4">
            {summaryHistoryQuery.data?.length ? (
              summaryHistoryQuery.data.map((item) => (
                <ResultPanel
                  key={item.id}
                  label={`摘要 #${item.id}`}
                  content={item.optimized_text}
                  meta={`保存时间：${new Date(item.created_at).toLocaleString()}`}
                />
              ))
            ) : (
              <EmptyHint>还没有摘要历史记录。</EmptyHint>
            )}
          </div>
        </SectionCard>
        <SectionCard title="优化历史" subtitle="这里展示之前保存过的优化建议记录。">
          <div className="space-y-4">
            {optimizationHistoryQuery.data?.length ? (
              optimizationHistoryQuery.data.map((item) => (
                <ResultPanel
                  key={item.id}
                  label={`优化建议 #${item.id}`}
                  content={item.optimized_text}
                  meta={`保存时间：${new Date(item.created_at).toLocaleString()}`}
                />
              ))
            ) : (
              <EmptyHint>还没有优化建议历史记录。</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
