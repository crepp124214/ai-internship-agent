import { useEffect, useState, type ChangeEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { interviewApi, readApiError, resumeApi, type GeneratedInterviewQuestion } from '../lib/api'
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

function formatEvaluationPreview(score: number, feedback: string) {
  return `Score: ${score}\n\n${feedback}`
}

const CONTEXT_JSON_KEYS = [
  'job_context',
  'description',
  'title',
  'context',
  'summary',
  'content',
  'requirements',
  'responsibilities',
  'role',
  'position',
  'jobDescription',
  'job_description',
  'jobTitle',
  'job_title',
  'company',
  'company_name',
] as const

function collectContextStrings(value: unknown, depth = 0): string[] {
  if (depth > 3) {
    return []
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed ? [trimmed] : []
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => collectContextStrings(item, depth + 1))
  }

  if (!value || typeof value !== 'object') {
    return []
  }

  const record = value as Record<string, unknown>
  const prioritized = CONTEXT_JSON_KEYS.flatMap((key) => collectContextStrings(record[key], depth + 1))
  if (prioritized.length > 0) {
    return prioritized
  }

  return Object.entries(record).flatMap(([key, candidate]) => {
    if (typeof candidate === 'string') {
      const trimmed = candidate.trim()
      return trimmed ? [`${key}: ${trimmed}`] : []
    }

    return collectContextStrings(candidate, depth + 1)
  })
}

function extractImportedContext(fileName: string, mimeType: string, rawContent: string) {
  const trimmedContent = rawContent.trim()
  if (!trimmedContent) {
    throw new Error('文件内容为空，请选择包含岗位上下文的文本或 JSON 文件。')
  }

  const isJsonFile = fileName.toLowerCase().endsWith('.json') || mimeType.includes('json')
  if (!isJsonFile) {
    return {
      content: trimmedContent,
      message: `已导入 ${fileName}，岗位上下文字段已更新。`,
    }
  }

  try {
    const parsed = JSON.parse(trimmedContent)
    const content = [...new Set(collectContextStrings(parsed))].join('\n\n').trim()

    if (content) {
      return {
        content,
        message: `已导入 ${fileName}，并从 JSON 中提取了结构化上下文。`,
      }
    }

      return {
        content: trimmedContent,
        message: `已导入 ${fileName}，但没有识别到明确字段，因此直接使用原始 JSON 文本。`,
      }
    } catch {
      return {
        content: trimmedContent,
        message: `已导入 ${fileName}，但 JSON 解析失败，因此改为直接使用原始文本。`,
      }
    }
}

export function InterviewPage() {
  const queryClient = useQueryClient()
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const questionsQuery = useQuery({ queryKey: ['interview', 'questions'], queryFn: interviewApi.listQuestions })
  const sessionsQuery = useQuery({ queryKey: ['interview', 'sessions'], queryFn: interviewApi.listSessions })
  const recordsQuery = useQuery({ queryKey: ['interview', 'records'], queryFn: interviewApi.listRecords })

  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(null)
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null)
  const [jobContext, setJobContext] = useState(
    '后端开发实习岗位，重点关注 FastAPI、异步接口、清晰架构和可维护的服务边界。',
  )
  const [answerText, setAnswerText] = useState('')
  const [questionCount, setQuestionCount] = useState(5)
  const [generatedQuestions, setGeneratedQuestions] = useState<GeneratedInterviewQuestion[]>([])
  const [selectedGeneratedQuestionIndex, setSelectedGeneratedQuestionIndex] = useState(0)
  const [answerPreview, setAnswerPreview] = useState<string | null>(null)
  const [recordResult, setRecordResult] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [contextImportState, setContextImportState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [contextImportMessage, setContextImportMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedResumeId && resumesQuery.data?.length) setSelectedResumeId(resumesQuery.data[0].id)
  }, [resumesQuery.data, selectedResumeId])

  useEffect(() => {
    if (!selectedQuestionId && questionsQuery.data?.length) setSelectedQuestionId(questionsQuery.data[0].id)
  }, [questionsQuery.data, selectedQuestionId])

  useEffect(() => {
    if (!selectedRecordId && recordsQuery.data?.length) setSelectedRecordId(recordsQuery.data[0].id)
  }, [recordsQuery.data, selectedRecordId])

  const selectedGeneratedQuestion = generatedQuestions[selectedGeneratedQuestionIndex] ?? null

  const handleContextImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const input = event.currentTarget
    const file = input.files?.[0]
    if (!file) {
      return
    }

    setContextImportState('loading')
      setContextImportMessage(`正在导入 ${file.name}...`)

    try {
      const rawContent = await file.text()
      const importedContext = extractImportedContext(file.name, file.type, rawContent)
      setJobContext(importedContext.content)
      setContextImportState('success')
      setContextImportMessage(importedContext.message)
    } catch (error) {
      setContextImportState('error')
      setContextImportMessage(error instanceof Error ? error.message : '导入失败，请稍后重试。')
    } finally {
      input.value = ''
    }
  }

  const createSessionMutation = useMutation({
    mutationFn: () =>
      interviewApi.createSession({
        session_type: 'technical',
        total_questions: questionCount,
        completed: 0,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['interview', 'sessions'] })
      setFeedback('面试会话已创建，后续题目和记录都可以挂在这次练习下。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const generateQuestionsMutation = useMutation({
    mutationFn: () =>
      interviewApi.generateQuestions({
        job_context: jobContext,
        resume_id: selectedResumeId,
        count: questionCount,
      }),
    onSuccess: (data) => {
      setGeneratedQuestions(data.questions)
      setSelectedGeneratedQuestionIndex(0)
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const saveGeneratedQuestionMutation = useMutation({
    mutationFn: () => {
      if (!selectedGeneratedQuestion) {
        throw new Error('请先生成题目，再选择其中一道保存。')
      }

      return interviewApi.createQuestion({
        question_type: selectedGeneratedQuestion.question_type,
        difficulty: selectedGeneratedQuestion.difficulty,
        question_text: selectedGeneratedQuestion.question_text,
        category: selectedGeneratedQuestion.category,
      })
    },
    onSuccess: async (question) => {
      await queryClient.invalidateQueries({ queryKey: ['interview', 'questions'] })
      setSelectedQuestionId(question.id)
      setFeedback(`生成的题目已保存到题库中（#${question.id}）。`)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const previewAnswerMutation = useMutation({
    mutationFn: () =>
      interviewApi.evaluateAnswer({
        question_text:
          questionsQuery.data?.find((item) => item.id === selectedQuestionId)?.question_text ??
          selectedGeneratedQuestion?.question_text ??
          '',
        user_answer: answerText,
        job_context: jobContext,
      }),
    onSuccess: (data) => {
      setAnswerPreview(formatEvaluationPreview(data.score, data.feedback))
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const createRecordMutation = useMutation({
    mutationFn: () => interviewApi.createRecord({ question_id: selectedQuestionId!, user_answer: answerText }),
    onSuccess: async (record) => {
      await queryClient.invalidateQueries({ queryKey: ['interview', 'records'] })
      setSelectedRecordId(record.id)
      setFeedback(`面试记录 #${record.id} 已创建，现在可以保存评估结果。`)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const evaluateRecordMutation = useMutation({
    mutationFn: () => interviewApi.evaluateRecord(selectedRecordId!, { job_context: jobContext }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['interview', 'records'] })
      setRecordResult(formatEvaluationPreview(data.score, `${data.feedback}\n\n${data.ai_evaluation}`))
      setFeedback('面试记录评估已保存。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="面试准备工作台"
        title="把题目、回答和评估串成一条可复盘的练习链路"
        description="生成面试题、预览回答评分、保存题目，并持续查看评估历史。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SectionCard
          title="生成题目"
          subtitle="结合岗位上下文和当前简历，生成更贴近真实场景的演示题目。"
        >
          <div className="space-y-4">
            <FormField
              label="导入本地上下文"
              helper="支持 txt、md 和 json，导入内容后会自动填回岗位上下文字段。"
            >
              <Input
                type="file"
                accept=".txt,.md,.json,text/plain,text/markdown,application/json"
                onChange={handleContextImport}
              />
            </FormField>
            {contextImportMessage ? (
              <div
                className={`rounded-[22px] px-4 py-3 text-sm ${
                  contextImportState === 'error'
                    ? 'border border-[rgba(207,72,72,0.24)] bg-[rgba(207,72,72,0.08)] text-[rgb(143,44,44)]'
                    : 'border border-[rgba(80,140,96,0.18)] bg-[rgba(80,140,96,0.08)] text-[rgb(42,102,58)]'
                }`}
              >
                {contextImportMessage}
              </div>
            ) : null}
            <FormField
                label="岗位上下文"
                helper="可以写岗位方向、技术栈、团队预期或业务背景，让生成题目更贴近实际。"
              >
              <Textarea value={jobContext} onChange={(event) => setJobContext(event.target.value)} className="min-h-40" />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="简历">
                <Select value={selectedResumeId ?? ''} onChange={(event) => setSelectedResumeId(Number(event.target.value))}>
                  {resumesQuery.data?.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      #{resume.id} - {resume.title}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="题目数量">
                <Input type="number" min={1} max={20} value={questionCount} onChange={(event) => setQuestionCount(Number(event.target.value))} />
              </FormField>
            </div>
            <div className="flex flex-wrap gap-3">
              <PrimaryButton type="button" onClick={() => generateQuestionsMutation.mutate()}>
                生成题目
              </PrimaryButton>
              <SecondaryButton type="button" onClick={() => createSessionMutation.mutate()}>
                创建面试会话
              </SecondaryButton>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="评估回答"
          subtitle="选择题目、写下回答、先看评分预览，再决定是否保存最终记录。"
        >
          <div className="space-y-4">
            {generatedQuestions.length ? (
              <FormField
                label="选择生成题目"
                helper="生成结果默认只用于预览，保存后才会进入题库。"
              >
                <div className="flex flex-col gap-3 md:flex-row">
                  <Select value={selectedGeneratedQuestionIndex} onChange={(event) => setSelectedGeneratedQuestionIndex(Number(event.target.value))}>
                    {generatedQuestions.map((question, index) => (
                      <option key={`${question.question_number}-${question.question_text}`} value={index}>
                        题目 {question.question_number} - {question.question_text.slice(0, 60)}
                      </option>
                    ))}
                  </Select>
                  <SecondaryButton type="button" onClick={() => saveGeneratedQuestionMutation.mutate()}>
                    保存生成题目
                  </SecondaryButton>
                </div>
              </FormField>
            ) : null}

            <FormField label="题库题目">
              <Select value={selectedQuestionId ?? ''} onChange={(event) => setSelectedQuestionId(Number(event.target.value))}>
                {questionsQuery.data?.map((question) => (
                  <option key={question.id} value={question.id}>
                    #{question.id} - {question.question_text.slice(0, 60)}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField
              label="你的回答"
              helper="尽量写完整回答。评估时会使用当前页面里的同一份岗位上下文。"
            >
              <Textarea value={answerText} onChange={(event) => setAnswerText(event.target.value)} className="min-h-40" />
            </FormField>
            <div className="flex flex-wrap gap-3">
              <SecondaryButton type="button" onClick={() => previewAnswerMutation.mutate()} disabled={!answerText.trim()}>
                预览回答评分
              </SecondaryButton>
              <SecondaryButton type="button" onClick={() => createRecordMutation.mutate()} disabled={!selectedQuestionId || !answerText.trim()}>
                创建面试记录
              </SecondaryButton>
              <PrimaryButton type="button" onClick={() => evaluateRecordMutation.mutate()} disabled={!selectedRecordId}>
                保存记录评估
              </PrimaryButton>
            </div>
            <FormField label="待评估记录">
              <Select value={selectedRecordId ?? ''} onChange={(event) => setSelectedRecordId(Number(event.target.value))}>
                {recordsQuery.data?.map((record) => (
                  <option key={record.id} value={record.id}>
                    记录 #{record.id} - 题目 {record.question_id}
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
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <SectionCard title="生成题目结果" subtitle="最新生成的一组题目会展示在这里，便于挑选和保存。">
          <div className="space-y-4">
            {generatedQuestions.length ? (
              generatedQuestions.map((question) => (
                <ResultPanel
                  key={`${question.question_number}-${question.question_text}`}
                  label={`题目 ${question.question_number}`}
                  content={question.question_text}
                  meta={`${question.question_type} - ${question.difficulty}`}
                />
              ))
            ) : (
              <EmptyHint>请先生成一组题目，这里才会显示结果。</EmptyHint>
            )}
          </div>
        </SectionCard>
        <SectionCard title="回答预览" subtitle="在保存记录前，先查看即时分数和反馈。">
          {answerPreview ? (
            <ResultPanel label="预览结果" content={answerPreview} />
          ) : (
            <EmptyHint>先写下回答并预览评分，这里才会出现即时反馈。</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="记录结果" subtitle="保存后的面试评估会保留在这里，方便继续复盘。">
          {recordResult ? (
            <ResultPanel label="已保存评估" content={recordResult} />
          ) : (
            <EmptyHint>请先创建记录，再保存评估结果，这里才会显示最终输出。</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="面试会话" subtitle="当前用户创建过的面试会话，按时间顺序展示。">
          <div className="space-y-4">
            {sessionsQuery.data?.length ? (
              sessionsQuery.data.map((session) => (
                <ResultPanel
                  key={session.id}
                  label={`会话 #${session.id}`}
                  content={`类型：${session.session_type}\n题目数：${session.total_questions ?? 0}\n完成数：${session.completed ?? 0}`}
                  meta={`创建时间：${session.created_at}`}
                />
              ))
            ) : (
              <EmptyHint>还没有面试会话记录。先创建一次会话，再把题目和记录串起来。</EmptyHint>
            )}
          </div>
        </SectionCard>
        <SectionCard title="面试记录" subtitle="记录是回答评估的持久化结果，也是后续复盘的依据。">
          <div className="space-y-4">
            {recordsQuery.data?.length ? (
              recordsQuery.data.map((record) => (
                <ResultPanel
                  key={record.id}
                  label={`记录 #${record.id}`}
                  content={record.ai_evaluation || record.user_answer}
                  meta={`分数 ${record.score ?? '暂无'} - ${record.created_at}`}
                />
              ))
            ) : (
              <EmptyHint>还没有面试记录。先保存一次回答，再沉淀可追踪历史。</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
