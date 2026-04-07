import { useEffect, useState, type ChangeEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { interviewApi, readApiError, resumeApi, type GeneratedInterviewQuestion, type ReviewReport } from '../lib/api'
import { ChatBubble } from './components/ChatBubble'
import { CoachReviewReportCard } from './components/CoachReviewReportCard'
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

const CONTEXT_JSON_KEYS = [
  'job_context', 'description', 'title', 'context', 'summary', 'content',
  'requirements', 'responsibilities', 'role', 'position',
  'jobDescription', 'job_description', 'jobTitle', 'job_title', 'company', 'company_name',
] as const

function collectContextStrings(value: unknown, depth = 0): string[] {
  if (depth > 3) return []
  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed ? [trimmed] : []
  }
  if (Array.isArray(value)) return value.flatMap((item) => collectContextStrings(item, depth + 1))
  if (!value || typeof value !== 'object') return []
  const record = value as Record<string, unknown>
  const prioritized = CONTEXT_JSON_KEYS.flatMap((key) => collectContextStrings(record[key], depth + 1))
  if (prioritized.length > 0) return prioritized
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
  if (!trimmedContent) throw new Error('文件内容为空')
  const isJsonFile = fileName.toLowerCase().endsWith('.json') || mimeType.includes('json')
  if (!isJsonFile) return { content: trimmedContent, message: `已导入 ${fileName}，岗位上下文字段已更新。` }
  try {
    const parsed = JSON.parse(trimmedContent)
    const content = [...new Set(collectContextStrings(parsed))].join('\n\n').trim()
    if (content) return { content, message: `已导入 ${fileName}，并从 JSON 中提取了结构化上下文。` }
    return { content: trimmedContent, message: `已导入 ${fileName}，没有识别到明确字段，使用原始 JSON 文本。` }
  } catch {
    return { content: trimmedContent, message: `已导入 ${fileName}，JSON 解析失败，使用原始文本。` }
  }
}

export function InterviewPage() {
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [jobContext, setJobContext] = useState('后端开发实习岗位，重点关注 FastAPI、异步接口、清晰架构和可维护的服务边界。')
  const [questionCount, setQuestionCount] = useState(5)
  const [generatedQuestions, setGeneratedQuestions] = useState<GeneratedInterviewQuestion[]>([])
  const [selectedGeneratedQuestionIndex, setSelectedGeneratedQuestionIndex] = useState(0)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [contextImportState, setContextImportState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [contextImportMessage, setContextImportMessage] = useState<string | null>(null)

  // Coach mode state
  const [coachActive, setCoachActive] = useState(false)
  const [coachSessionId, setCoachSessionId] = useState<number | null>(null)
  const [coachMessages, setCoachMessages] = useState<Array<{role: 'ai' | 'user', message: string, score?: number | null}>>([])
  const [coachAnswer, setCoachAnswer] = useState('')
  const [coachFeedback, setCoachFeedback] = useState<string | null>(null)
  const [coachReport, setCoachReport] = useState<ReviewReport | null>(null)
  const [isLast, setIsLast] = useState(false)
  const [inFollowup, setInFollowup] = useState(false)

  useEffect(() => {
    if (!selectedResumeId && resumesQuery.data?.length) setSelectedResumeId(resumesQuery.data[0].id)
  }, [resumesQuery.data, selectedResumeId])

  const selectedGeneratedQuestion = generatedQuestions[selectedGeneratedQuestionIndex] ?? null

  const handleContextImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const input = event.currentTarget
    const file = input.files?.[0]
    if (!file) return
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
      setContextImportMessage(error instanceof Error ? error.message : '导入失败')
    } finally {
      input.value = ''
    }
  }

  const generateQuestionsMutation = useMutation({
    mutationFn: () => interviewApi.generateQuestions({ job_context: jobContext, resume_id: selectedResumeId, count: questionCount }),
    onSuccess: (data) => {
      setGeneratedQuestions(data.questions)
      setSelectedGeneratedQuestionIndex(0)
      setFeedback(null)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const saveGeneratedQuestionMutation = useMutation({
    mutationFn: () => {
      if (!selectedGeneratedQuestion) throw new Error('请先生成题目')
      return interviewApi.createQuestion({
        question_type: selectedGeneratedQuestion.question_type,
        difficulty: selectedGeneratedQuestion.difficulty,
        question_text: selectedGeneratedQuestion.question_text,
        category: selectedGeneratedQuestion.category,
      })
    },
    onSuccess: async () => {
      setFeedback('题目已保存到题库。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const startCoachMutation = useMutation({
    mutationFn: ({ resumeId }: { resumeId: number }) => interviewApi.coachStart({ resume_id: resumeId }),
    onSuccess: (data) => {
      setCoachSessionId(data.session_id)
      setCoachMessages([
        { role: 'ai', message: data.opening_message },
        { role: 'ai', message: data.first_question },
      ])
      setIsLast(false)
      setInFollowup(false)
      setCoachActive(true)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const submitAnswerMutation = useMutation({
    mutationFn: ({ sessionId, answer }: { sessionId: number; answer: string }) =>
      interviewApi.coachAnswer({ session_id: sessionId, answer }),
    onSuccess: (data) => {
      setCoachMessages((prev) => [
        ...prev,
        { role: 'user', message: coachAnswer },
        { role: 'ai', message: data.feedback, score: data.score },
      ])
      setCoachFeedback(`本题得分：${data.score}分 - ${data.feedback}`)
      setCoachAnswer('')
      if (data.next_question) {
        setCoachMessages((prev) => [...prev, { role: 'ai', message: data.next_question! }])
        setIsLast(data.is_last)
      } else {
        setInFollowup(true)
      }
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const endCoachMutation = useMutation({
    mutationFn: ({ sessionId, followupSkipped }: { sessionId: number; followupSkipped: boolean }) =>
      interviewApi.coachEnd(sessionId, followupSkipped),
    onSuccess: (data) => {
      setCoachReport(data.review_report)
      setCoachActive(false)
      setFeedback('面试已结束，复盘报告已生成。')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="面试准备工作台"
        title="生成面试题目，进行 AI 对练"
        description="生成针对性的面试题目，或直接进入 AI 面试教练进行多轮对练。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SectionCard title="生成题目" subtitle="结合岗位上下文和简历，生成针对性面试题目。">
          <div className="space-y-4">
            <FormField label="导入本地上下文" helper="支持 txt、md 和 json 文件。">
              <Input
                type="file"
                accept=".txt,.md,.json,text/plain,text/markdown,application/json"
                onChange={handleContextImport}
              />
            </FormField>
            {contextImportMessage ? (
              <div className={`rounded-[22px] px-4 py-3 text-sm ${
                contextImportState === 'error'
                  ? 'border border-[rgba(207,72,72,0.24)] bg-[rgba(207,72,72,0.08)] text-[rgb(143,44,44)]'
                  : 'border border-[rgba(80,140,96,0.18)] bg-[rgba(80,140,96,0.08)] text-[rgb(42,102,58)]'
              }`}>
                {contextImportMessage}
              </div>
            ) : null}
            <FormField label="岗位上下文" helper="描述岗位方向、技术栈、业务背景等。">
              <Textarea value={jobContext} onChange={(event) => setJobContext(event.target.value)} className="min-h-32" />
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
            <PrimaryButton type="button" onClick={() => generateQuestionsMutation.mutate()}>
              生成题目
            </PrimaryButton>
          </div>
        </SectionCard>

        <SectionCard title="面试教练" subtitle="选择简历后直接开始 AI 面试对练。">
          {coachActive ? (
            <div className="space-y-4">
              <div className="flex flex-col gap-2 max-h-80 overflow-y-auto">
                {coachMessages.map((msg, i) => (
                  <ChatBubble key={i} role={msg.role} message={msg.message} score={msg.score} />
                ))}
              </div>
              {coachFeedback ? (
                <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm">
                  {coachFeedback}
                </div>
              ) : null}
              <div className="flex gap-3">
                <Textarea
                  value={coachAnswer}
                  onChange={(e) => setCoachAnswer(e.target.value)}
                  placeholder="输入你的回答..."
                  className="flex-1"
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <SecondaryButton
                  type="button"
                  onClick={() => submitAnswerMutation.mutate({ sessionId: coachSessionId!, answer: coachAnswer })}
                  disabled={!coachAnswer.trim()}
                >
                  提交回答
                </SecondaryButton>
                <PrimaryButton
                  type="button"
                  onClick={() => endCoachMutation.mutate({ sessionId: coachSessionId!, followupSkipped: inFollowup })}
                >
                  结束面试
                </PrimaryButton>
              </div>
            </div>
          ) : coachReport ? (
            <div className="space-y-4">
              <CoachReviewReportCard report={coachReport} />
              <SecondaryButton type="button" onClick={() => { setCoachReport(null); setCoachMessages([]) }}>
                重新开始
              </SecondaryButton>
            </div>
          ) : (
            <div className="space-y-4">
              <EmptyHint>选择简历后点击开始，进入 AI 面试教练对练。</EmptyHint>
              <PrimaryButton
                type="button"
                onClick={() => startCoachMutation.mutate({ resumeId: selectedResumeId! })}
                disabled={!selectedResumeId}
              >
                开始面试教练
              </PrimaryButton>
            </div>
          )}
        </SectionCard>
      </div>

      {generatedQuestions.length > 0 && (
        <SectionCard title="生成的题目" subtitle="选择一道题目保存到题库。">
          <div className="space-y-4">
            <FormField label="选择题目">
              <Select
                value={selectedGeneratedQuestionIndex}
                onChange={(event) => setSelectedGeneratedQuestionIndex(Number(event.target.value))}
              >
                {generatedQuestions.map((question, index) => (
                  <option key={`${question.question_number}-${question.question_text}`} value={index}>
                    题目 {question.question_number} - {question.question_text.slice(0, 60)}
                  </option>
                ))}
              </Select>
            </FormField>
            {selectedGeneratedQuestion && (
              <ResultPanel
                label={`题目 ${selectedGeneratedQuestion.question_number}`}
                content={selectedGeneratedQuestion.question_text}
                meta={`${selectedGeneratedQuestion.question_type} - ${selectedGeneratedQuestion.difficulty}`}
              />
            )}
            <SecondaryButton type="button" onClick={() => saveGeneratedQuestionMutation.mutate()}>
              保存到题库
            </SecondaryButton>
            {feedback && (
              <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm">{feedback}</div>
            )}
          </div>
        </SectionCard>
      )}
    </div>
  )
}
