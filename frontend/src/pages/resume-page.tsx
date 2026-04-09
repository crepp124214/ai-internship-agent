// frontend/src/pages/resume-page.tsx
import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { jobsApi, readApiError, resumeApi, type MatchReportData, type Resume } from '../lib/api'
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
import { MatchReportCard } from './components/MatchReportCard'
import { FloatingToolbar } from './components/FloatingToolbar'
import { ResumeDiffView } from './components/ResumeDiffView'

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

export function ResumePage() {
  const queryClient = useQueryClient()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [createTitle, setCreateTitle] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [importStatus, setImportStatus] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [selectedImportFile, setSelectedImportFile] = useState<File | null>(null)
  const [importInputKey, setImportInputKey] = useState(0)
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

    if (flowTargetRole && !targetRole.trim()) {
      setTargetRole(flowTargetRole)
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
  }, [location.state, searchParams, targetRole])

  useEffect(() => {
    if (!selectedJobId && jobsQuery.data?.length) {
      setSelectedJobId(jobsQuery.data[0].id)
    }
  }, [jobsQuery.data, selectedJobId])

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
    onSuccess: async ({ updatedResume, fileName }) => {
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
    onSuccess: (data) => {
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

  // Floating toolbar handlers
  const handleFloatingOptimize = (selectedText: string) => {
    // For now, just show the text being optimized
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

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="简历优化"
        title="选择简历并进行 JD 定向优化"
        description="从已有简历中选择版本，结合目标岗位生成摘要与优化建议。"
      />

      <div className="grid gap-6 xl:grid-cols-2">
        {/* 左侧：创建/导入 */}
        <SectionCard title="创建 / 导入简历" subtitle="整理出一份基础简历，再进行 AI 分析。">
          <div className="space-y-5">
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

            <FormField label="导入本地简历" helper="支持 txt、md 和 json 文件。">
              <div className="space-y-3">
                <input
                  key={importInputKey}
                  type="file"
                  accept=".txt,.md,.json,text/plain,application/json"
                  onChange={handleImportFileChange}
                  className="w-full rounded-2xl border border-[var(--color-border)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition file:mr-4 file:rounded-full file:border-0 file:bg-[var(--color-accent)] file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]"
                />
                 {selectedImportFile ? (
                   <p className="text-sm text-[var(--color-ink)]">已选择：{selectedImportFile.name}</p>
                 ) : (
                   <p className="text-sm text-[var(--color-ink-muted)]">选择文件后点击"导入并创建"</p>
                 )}
                 {importStatus ? (
                   <p className="text-xs leading-5 text-[var(--color-ink-muted)]">{importStatus}</p>
                 ) : null}
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
                  <p className="text-xs leading-5 text-[var(--color-ink-muted)]">{importStatus}</p>
                ) : null}
              </div>
            </FormField>

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
                    #{job.id} - {job.title} @ {job.company}
                  </option>
                ))}
              </Select>
            </FormField>

            <FormField label="JD 优化指令（可选）" helper="例如：突出 Python + FastAPI 项目经历">
              <Textarea
                value={jdInstructions}
                onChange={(event) => setJdInstructions(event.target.value)}
                className="min-h-24"
              />
            </FormField>

            <PrimaryButton
              type="button"
              onClick={() => customizeForJdMutation.mutate()}
              disabled={!effectiveSelectedResumeId || !selectedJobId || customizeForJdMutation.isPending}
            >
              {customizeForJdMutation.isPending ? '优化中...' : '开始 JD 定向优化'}
            </PrimaryButton>

            {flowHint ? (
              <div className="rounded-2xl bg-[rgba(86,128,99,0.12)] px-4 py-3 text-sm text-[var(--color-ink)]">
                {flowHint}
              </div>
            ) : null}

            {feedback ? (
              <div className="rounded-2xl bg-[var(--color-surface-sunken)] px-4 py-3 text-sm text-[var(--color-ink)]">
                {feedback}
              </div>
            ) : null}
          </div>
        </SectionCard>

        {/* 右侧：简历列表 */}
        <SectionCard title="简历列表" subtitle="选择简历后可预览内容。">
          <div className="space-y-4">
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

            {resumesQuery.isLoading ? (
              <div className="text-sm text-[var(--color-ink-tertiary)]">加载中...</div>
            ) : resumesQuery.data?.length === 0 ? (
              <EmptyHint>暂无简历数据，请先创建或导入一份简历。</EmptyHint>
            ) : effectiveSelectedResume ? (
              <>
                <div
                  ref={resumeContentRef}
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
                >
                  <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--color-ink)]">
                    {resumeText || '（简历内容为空）'}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <SecondaryButton
                    type="button"
                    onClick={() => summaryPreviewMutation.mutate()}
                    disabled={!effectiveSelectedResumeId || !resumeText || summaryPreviewMutation.isPending}
                  >
                    预览摘要
                  </SecondaryButton>
                  <SecondaryButton
                    type="button"
                    onClick={() => improvementsPreviewMutation.mutate()}
                    disabled={!effectiveSelectedResumeId || !resumeText || improvementsPreviewMutation.isPending}
                  >
                    预览优化
                  </SecondaryButton>
                </div>
              </>
            ) : (
              <EmptyHint>请先创建或导入一份简历。</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>

      {/* Floating Toolbar - appears when text is selected */}
      <FloatingToolbar
        targetRef={resumeContentRef}
        onOptimize={handleFloatingOptimize}
        onSummarize={handleFloatingSummarize}
        onExplain={handleFloatingExplain}
      />

      {/* Diff 视图 - Cursor 风格 */}
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

      {/* 下方：摘要和优化建议 */}
      {(summaryPreview || improvementsPreview || customizedResume || matchReport) && !showDiff && (
        <div className="grid gap-6 xl:grid-cols-2">
          <SectionCard title="简历摘要" subtitle="AI 生成的简历摘要。">
            {summaryPreview ? (
              <ResultPanel label="摘要" content={summaryPreview} />
            ) : (
              <EmptyHint>点击上方「预览摘要」</EmptyHint>
            )}
          </SectionCard>
          <SectionCard title="优化建议" subtitle="AI 提供的简历改写建议。">
            {improvementsPreview ? (
              <ResultPanel label="优化建议" content={improvementsPreview} />
            ) : (
              <EmptyHint>点击上方「预览优化」</EmptyHint>
            )}
          </SectionCard>
          <SectionCard title="JD 定向优化结果" subtitle="基于目标岗位重写后的简历内容。">
            {customizedResume ? (
              <ResultPanel label="定向优化简历" content={customizedResume} />
            ) : (
              <EmptyHint>点击上方「开始 JD 定向优化」</EmptyHint>
            )}
          </SectionCard>
          <SectionCard title="匹配报告" subtitle="当前简历与目标岗位的匹配分析。">
            {matchReport ? <MatchReportCard report={matchReport} /> : <EmptyHint>完成定向优化后显示报告</EmptyHint>}
          </SectionCard>
        </div>
      )}
    </div>
  )
}
