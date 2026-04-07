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
  if (lastDotIndex < 0) return ''
  return fileName.slice(lastDotIndex + 1).toLowerCase()
}

function stripFileExtension(fileName: string) {
  const lastDotIndex = fileName.lastIndexOf('.')
  if (lastDotIndex < 0) return fileName
  return fileName.slice(0, lastDotIndex)
}

function sanitizeFileName(fileName: string) {
  return fileName.replace(/[^a-zA-Z0-9._-]+/g, '-')
}

function resolveResumeTitle(manualTitle: string, file: File) {
  const trimmedTitle = manualTitle.trim()
  if (trimmedTitle) return trimmedTitle
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

  const resumeText = effectiveSelectedResume?.processed_content ?? effectiveSelectedResume?.resume_text ?? ''

  const createResumeMutation = useMutation({
    mutationFn: ({ title, filePath }: { title: string; filePath: string }) =>
      resumeApi.create({ title, file_path: filePath }),
    onSuccess: async (resume) => {
      queryClient.setQueryData<Resume[]>(['resume', 'list'], (current = []) => [
        resume,
        ...(current ?? []).filter((item) => item.id !== resume.id),
      ])
      await queryClient.invalidateQueries({ queryKey: ['resume', 'list'] })
      setSelectedResumeId(resume.id)
      setCreateTitle('')
      setFeedback('简历创建成功。')
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
      return { updatedResume, resolvedTitle, fileText, fileName: file.name }
    },
    onSuccess: async ({ updatedResume, resolvedTitle, fileText, fileName }) => {
      queryClient.setQueryData<Resume[]>(['resume', 'list'], (current = []) => [
        updatedResume,
        ...(current ?? []).filter((item) => item.id !== updatedResume.id),
      ])
      await queryClient.invalidateQueries({ queryKey: ['resume', 'list'] })
      setSelectedResumeId(updatedResume.id)
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

  const summaryPreviewMutation = useMutation({
    mutationFn: () => resumeApi.previewSummary(effectiveSelectedResumeId!, { target_role: targetRole || null }),
    onSuccess: (data) => setSummaryPreview(data.content),
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
    onSuccess: (data) => setImprovementsPreview(data.content),
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
        title="一次整理，持续优化简历内容"
        description="创建或导入简历，预览 AI 摘要与优化建议。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <SectionCard title="创建 / 导入简历" subtitle="整理出一份基础简历，再进行 AI 优化。">
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
              label="导入本地简历"
              helper="支持 txt、md 和 json 文件。"
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
                  <p className="text-sm text-[var(--color-muted)]">选择文件后点击"导入并创建"</p>
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
            <FormField label="选择简历">
              <Select
                value={selectedResumeId ?? ''}
                onChange={(event) => setSelectedResumeId(Number(event.target.value))}
              >
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} - {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="目标岗位">
              <Input
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder="例如：后端开发实习生"
              />
            </FormField>
            {feedback ? (
              <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
                {feedback}
              </div>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="简历内容" subtitle="选择简历后可预览摘要和优化建议。">
          {effectiveSelectedResume ? (
            <div className="space-y-4">
              <div className="rounded-[24px] border border-[var(--color-stroke)] bg-[var(--color-surface)] p-5">
                <p className="text-sm leading-7 whitespace-pre-wrap text-[var(--color-ink)]">
                  {resumeText || '（简历内容为空）'}
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <SecondaryButton
                  type="button"
                  onClick={() => summaryPreviewMutation.mutate()}
                  disabled={!effectiveSelectedResumeId || !resumeText}
                >
                  预览摘要
                </SecondaryButton>
                <SecondaryButton
                  type="button"
                  onClick={() => summaryPersistMutation.mutate()}
                  disabled={!effectiveSelectedResumeId || !resumeText}
                >
                  保存摘要
                </SecondaryButton>
                <SecondaryButton
                  type="button"
                  onClick={() => improvementsPreviewMutation.mutate()}
                  disabled={!effectiveSelectedResumeId || !resumeText}
                >
                  预览优化建议
                </SecondaryButton>
                <SecondaryButton
                  type="button"
                  onClick={() => improvementsPersistMutation.mutate()}
                  disabled={!effectiveSelectedResumeId || !resumeText}
                >
                  保存优化建议
                </SecondaryButton>
              </div>
            </div>
          ) : (
            <EmptyHint>请先创建或导入一份简历。</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="摘要" subtitle="预览或保存 AI 生成的简历摘要。">
          {summaryPreview ? (
            <ResultPanel label="摘要" content={summaryPreview} />
          ) : (
            <EmptyHint>先预览或保存摘要，这里才会显示内容。</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="优化建议" subtitle="AI 提供的简历改写和增强建议。">
          {improvementsPreview ? (
            <ResultPanel label="优化建议" content={improvementsPreview} />
          ) : (
            <EmptyHint>先预览或保存优化建议，这里才会显示内容。</EmptyHint>
          )}
        </SectionCard>
      </div>
    </div>
  )
}
