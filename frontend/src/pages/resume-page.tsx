import { useEffect, useMemo, useState, type ChangeEvent } from 'react'
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
  const safeTitle = sanitizeFileName(title.trim() || 'resume')
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
    reader.onerror = () => reject(reader.error ?? new Error('读取文件失败'))
    reader.readAsText(file)
  })
}

export function ResumePage() {
  const queryClient = useQueryClient()
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [createTitle, setCreateTitle] = useState('')
  const [editTitle, setEditTitle] = useState('')
  const [resumeText, setResumeText] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [importStatus, setImportStatus] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [selectedImportFile, setSelectedImportFile] = useState<File | null>(null)
  const [importInputKey, setImportInputKey] = useState(0)
  const [summaryPreview, setSummaryPreview] = useState<string | null>(null)
  const [improvementsPreview, setImprovementsPreview] = useState<string | null>(null)

  const selectedResume = useMemo(
    () => resumesQuery.data?.find((resume) => resume.id === selectedResumeId) ?? null,
    [resumesQuery.data, selectedResumeId],
  )

  useEffect(() => {
    if (!selectedResumeId && resumesQuery.data?.length) {
      setSelectedResumeId(resumesQuery.data[0].id)
    }
  }, [resumesQuery.data, selectedResumeId])

  useEffect(() => {
    if (selectedResume) {
      setEditTitle(selectedResume.title)
      setResumeText(selectedResume.processed_content ?? selectedResume.resume_text ?? '')
    }
  }, [selectedResume])

  const summaryHistoryQuery = useQuery({
    queryKey: ['resume', 'summary-history', selectedResumeId],
    queryFn: () => resumeApi.getSummaryHistory(selectedResumeId!),
    enabled: Boolean(selectedResumeId),
  })

  const optimizationHistoryQuery = useQuery({
    queryKey: ['resume', 'optimization-history', selectedResumeId],
    queryFn: () => resumeApi.getOptimizationHistory(selectedResumeId!),
    enabled: Boolean(selectedResumeId),
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
      setFeedback('简历创建成功')
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
      setEditTitle(resume.title)
      setResumeText(resume.processed_content ?? resume.resume_text ?? '')
      setFeedback('简历内容已更新')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const summaryPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewSummary(selectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => setSummaryPreview(data.content),
    onError: (error) => setFeedback(readApiError(error)),
  })

  const summaryPersistMutation = useMutation({
    mutationFn: () => resumeApi.persistSummary(selectedResumeId!, { target_role: targetRole || null }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['resume', 'summary-history', selectedResumeId] })
      setSummaryPreview(data.optimized_text)
      setFeedback('摘要已保存到历史记录')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const improvementsPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewImprovements(selectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => setImprovementsPreview(data.content),
    onError: (error) => setFeedback(readApiError(error)),
  })

  const improvementsPersistMutation = useMutation({
    mutationFn: () => resumeApi.persistImprovements(selectedResumeId!, { target_role: targetRole || null }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['resume', 'optimization-history', selectedResumeId] })
      setImprovementsPreview(data.optimized_text)
      setFeedback('优化建议已保存到历史记录')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const importResumeMutation = useMutation({
    mutationFn: async ({ file, title }: { file: File; title: string }) => {
      if (!isSupportedResumeImport(file)) {
        throw new Error('只支持 txt、md、json 文本简历文件')
      }

      const resolvedTitle = resolveResumeTitle(title, file)

      setImportStatus(`正在读取 ${file.name}`)
      const fileText = await readTextFile(file)

      setImportStatus(`正在创建 ${file.name}`)
      const createdResume = await resumeApi.create({
        title: resolvedTitle,
        file_path: buildImportedFilePath(file),
      })

      setImportStatus(`正在写入 ${file.name}`)
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
      setEditTitle(updatedResume.title || resolvedTitle)
      setResumeText(updatedResume.processed_content ?? updatedResume.resume_text ?? fileText)
      setCreateTitle('')
      setSelectedImportFile(null)
      setImportStatus(`已导入 ${fileName}`)
      setFeedback('简历导入并写入成功')
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
      setFeedback('只支持 txt、md、json 文本简历文件')
      setImportInputKey((value) => value + 1)
      return
    }

    setSelectedImportFile(file)
    setImportStatus(`已选择 ${file.name}`)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="简历中心"
        title="一次编辑，保留每次 AI 迭代的轨迹"
        description="在这里统一管理简历内容、摘要预览与保存、优化建议预览与保存，以及两条历史记录。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <SectionCard title="简历列表" subtitle="先手动创建一份简历，再在岗位、面试和投递流程里持续复用。">
          <div className="space-y-4">
            <FormField label="新建简历">
              <div className="flex flex-col gap-3 md:flex-row">
                <Input
                  value={createTitle}
                  onChange={(event) => setCreateTitle(event.target.value)}
                  placeholder="2026 届实习求职主简历"
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
              label="导入本地文本简历"
              helper="支持 txt、md、json。浏览器会先读取文件内容，再创建并写回正文。"
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
                  <p className="text-sm text-[var(--color-muted)]">先选择一个本地文本文件，再点击导入创建简历。</p>
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
                  {importResumeMutation.isPending ? '导入中…' : '导入并创建'}
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
                    #{resume.id} · {resume.title}
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
          subtitle="当前版本会把同一份内容同时写入 processed_content 与 resume_text，方便保持演示链路的一致性。"
        >
          {selectedResume ? (
            <div className="space-y-4">
              <FormField label="标题">
                <Input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} />
              </FormField>
              <FormField
                label="简历正文"
                helper="后端会优先读取 processed_content，缺失时再回退到 resume_text。当前页会同时写入这两个字段。"
              >
                <Textarea value={resumeText} onChange={(event) => setResumeText(event.target.value)} className="min-h-56" />
              </FormField>
              <FormField label="目标岗位">
                <Input value={targetRole} onChange={(event) => setTargetRole(event.target.value)} placeholder="后端开发实习生" />
              </FormField>
              <div className="flex flex-wrap gap-3">
                <PrimaryButton
                  type="button"
                  onClick={() => updateResumeMutation.mutate({ resume: selectedResume, title: editTitle, resumeText })}
                >
                  保存简历
                </PrimaryButton>
                <SecondaryButton type="button" onClick={() => summaryPreviewMutation.mutate()} disabled={!selectedResumeId}>
                  预览摘要
                </SecondaryButton>
                <SecondaryButton type="button" onClick={() => summaryPersistMutation.mutate()} disabled={!selectedResumeId}>
                  保存摘要
                </SecondaryButton>
                <SecondaryButton type="button" onClick={() => improvementsPreviewMutation.mutate()} disabled={!selectedResumeId}>
                  预览优化
                </SecondaryButton>
                <SecondaryButton type="button" onClick={() => improvementsPersistMutation.mutate()} disabled={!selectedResumeId}>
                  保存优化
                </SecondaryButton>
              </div>
            </div>
          ) : (
            <EmptyHint>请先创建简历，再解锁摘要、优化和后续匹配能力。</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="摘要" subtitle="预览不会写入历史，保存后才会生成可追溯记录。">
          {summaryPreview ? (
            <ResultPanel label="摘要预览" content={summaryPreview} />
          ) : (
            <EmptyHint>使用“预览摘要”或“保存摘要”查看最新结果。</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="优化建议" subtitle="这部分结果适合用来展示 AI 对简历内容的润色与补强。">
          {improvementsPreview ? (
            <ResultPanel label="优化预览" content={improvementsPreview} />
          ) : (
            <EmptyHint>使用优化相关操作，生成可执行的改写建议。</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="摘要历史" subtitle="已经保存过的摘要记录。">
          <div className="space-y-4">
            {summaryHistoryQuery.data?.length ? (
              summaryHistoryQuery.data.map((item) => (
                <ResultPanel
                  key={item.id}
                  label={`摘要 #${item.id}`}
                  content={item.optimized_text}
                  meta={`保存时间 ${new Date(item.created_at).toLocaleString()}`}
                />
              ))
            ) : (
              <EmptyHint>暂时还没有摘要历史。</EmptyHint>
            )}
          </div>
        </SectionCard>
        <SectionCard title="优化历史" subtitle="已经保存过的优化记录。">
          <div className="space-y-4">
            {optimizationHistoryQuery.data?.length ? (
              optimizationHistoryQuery.data.map((item) => (
                <ResultPanel
                  key={item.id}
                  label={`优化 #${item.id}`}
                  content={item.optimized_text}
                  meta={`保存时间 ${new Date(item.created_at).toLocaleString()}`}
                />
              ))
            ) : (
              <EmptyHint>暂时还没有优化历史。</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
