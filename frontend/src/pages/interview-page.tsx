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
    throw new Error('The file is empty. Choose a text or JSON file with job context.')
  }

  const isJsonFile = fileName.toLowerCase().endsWith('.json') || mimeType.includes('json')
  if (!isJsonFile) {
    return {
      content: trimmedContent,
      message: `Imported ${fileName}. The job context field was updated.`,
    }
  }

  try {
    const parsed = JSON.parse(trimmedContent)
    const content = [...new Set(collectContextStrings(parsed))].join('\n\n').trim()

    if (content) {
      return {
        content,
        message: `Imported ${fileName}. Extracted structured context from JSON.`,
      }
    }

    return {
      content: trimmedContent,
      message: `Imported ${fileName}. No obvious fields were found, so the raw JSON text was used.`,
    }
  } catch {
    return {
      content: trimmedContent,
      message: `Imported ${fileName}. JSON parsing failed, so the raw text was used instead.`,
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
    'Backend engineering internship focused on FastAPI, async APIs, clear architecture, and maintainable service boundaries.',
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
    setContextImportMessage(`Importing ${file.name}...`)

    try {
      const rawContent = await file.text()
      const importedContext = extractImportedContext(file.name, file.type, rawContent)
      setJobContext(importedContext.content)
      setContextImportState('success')
      setContextImportMessage(importedContext.message)
    } catch (error) {
      setContextImportState('error')
      setContextImportMessage(error instanceof Error ? error.message : 'Import failed. Please try again.')
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
      setFeedback('Interview session created. Future questions and records can now be tied back to it.')
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
        throw new Error('Generate questions first, then choose one to save.')
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
      setFeedback(`Generated question saved to the question bank (#${question.id}).`)
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
      setFeedback(`Interview record #${record.id} created. You can now save the evaluation result.`)
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const evaluateRecordMutation = useMutation({
    mutationFn: () => interviewApi.evaluateRecord(selectedRecordId!, { job_context: jobContext }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['interview', 'records'] })
      setRecordResult(formatEvaluationPreview(data.score, `${data.feedback}\n\n${data.ai_evaluation}`))
      setFeedback('Interview record evaluation saved.')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Interview Prep Workspace"
        title="Connect generated questions, answers, and evaluations in one review loop"
        description="Generate interview questions, preview answer scoring, save questions, and keep evaluation history visible."
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SectionCard
          title="Generate Questions"
          subtitle="Use job context and the selected resume to create a realistic set of demo interview questions."
        >
          <div className="space-y-4">
            <FormField
              label="Import local context"
              helper="Supports txt, md, and json. The imported content will refill the job context field."
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
              label="Job context"
              helper="Include role direction, stack, team expectations, or business context so the generated questions stay grounded."
            >
              <Textarea value={jobContext} onChange={(event) => setJobContext(event.target.value)} className="min-h-40" />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Resume">
                <Select value={selectedResumeId ?? ''} onChange={(event) => setSelectedResumeId(Number(event.target.value))}>
                  {resumesQuery.data?.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      #{resume.id} - {resume.title}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Question count">
                <Input type="number" min={1} max={20} value={questionCount} onChange={(event) => setQuestionCount(Number(event.target.value))} />
              </FormField>
            </div>
            <div className="flex flex-wrap gap-3">
              <PrimaryButton type="button" onClick={() => generateQuestionsMutation.mutate()}>
                Generate questions
              </PrimaryButton>
              <SecondaryButton type="button" onClick={() => createSessionMutation.mutate()}>
                Create interview session
              </SecondaryButton>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="Evaluate an Answer"
          subtitle="Choose a question, write an answer, preview the score, then save the final record."
        >
          <div className="space-y-4">
            {generatedQuestions.length ? (
              <FormField
                label="Choose a generated question"
                helper="Generated results are preview-only until you save one into the question bank."
              >
                <div className="flex flex-col gap-3 md:flex-row">
                  <Select value={selectedGeneratedQuestionIndex} onChange={(event) => setSelectedGeneratedQuestionIndex(Number(event.target.value))}>
                    {generatedQuestions.map((question, index) => (
                      <option key={`${question.question_number}-${question.question_text}`} value={index}>
                        Q{question.question_number} - {question.question_text.slice(0, 60)}
                      </option>
                    ))}
                  </Select>
                  <SecondaryButton type="button" onClick={() => saveGeneratedQuestionMutation.mutate()}>
                    Save generated question
                  </SecondaryButton>
                </div>
              </FormField>
            ) : null}

            <FormField label="Question bank item">
              <Select value={selectedQuestionId ?? ''} onChange={(event) => setSelectedQuestionId(Number(event.target.value))}>
                {questionsQuery.data?.map((question) => (
                  <option key={question.id} value={question.id}>
                    #{question.id} - {question.question_text.slice(0, 60)}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField
              label="Your answer"
              helper="Write a complete answer. The evaluator uses the same job context shown on this page."
            >
              <Textarea value={answerText} onChange={(event) => setAnswerText(event.target.value)} className="min-h-40" />
            </FormField>
            <div className="flex flex-wrap gap-3">
              <SecondaryButton type="button" onClick={() => previewAnswerMutation.mutate()} disabled={!answerText.trim()}>
                Preview answer score
              </SecondaryButton>
              <SecondaryButton type="button" onClick={() => createRecordMutation.mutate()} disabled={!selectedQuestionId || !answerText.trim()}>
                Create interview record
              </SecondaryButton>
              <PrimaryButton type="button" onClick={() => evaluateRecordMutation.mutate()} disabled={!selectedRecordId}>
                Save record evaluation
              </PrimaryButton>
            </div>
            <FormField label="Record to evaluate">
              <Select value={selectedRecordId ?? ''} onChange={(event) => setSelectedRecordId(Number(event.target.value))}>
                {recordsQuery.data?.map((record) => (
                  <option key={record.id} value={record.id}>
                    Record #{record.id} - Question {record.question_id}
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
        <SectionCard title="Generated Questions" subtitle="The latest generated set stays here for review and saving.">
          <div className="space-y-4">
            {generatedQuestions.length ? (
              generatedQuestions.map((question) => (
                <ResultPanel
                  key={`${question.question_number}-${question.question_text}`}
                  label={`Question ${question.question_number}`}
                  content={question.question_text}
                  meta={`${question.question_type} - ${question.difficulty}`}
                />
              ))
            ) : (
              <EmptyHint>Generate a question set first to populate this panel.</EmptyHint>
            )}
          </div>
        </SectionCard>
        <SectionCard title="Answer Preview" subtitle="See the instant score and feedback before you persist a record.">
          {answerPreview ? (
            <ResultPanel label="Preview result" content={answerPreview} />
          ) : (
            <EmptyHint>Write an answer and preview the score to see instant feedback.</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="Record Result" subtitle="Saved interview evaluations remain visible here for follow-up review.">
          {recordResult ? (
            <ResultPanel label="Saved evaluation" content={recordResult} />
          ) : (
            <EmptyHint>Create a record first, then save the evaluation result to see the final output here.</EmptyHint>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Sessions" subtitle="Interview sessions created by the current user, shown in time order.">
          <div className="space-y-4">
            {sessionsQuery.data?.length ? (
              sessionsQuery.data.map((session) => (
                <ResultPanel
                  key={session.id}
                  label={`Session #${session.id}`}
                  content={`Type: ${session.session_type}\nQuestions: ${session.total_questions ?? 0}\nCompleted: ${session.completed ?? 0}`}
                  meta={`Created at ${session.created_at}`}
                />
              ))
            ) : (
              <EmptyHint>No interview sessions yet. Create one first to connect questions and records.</EmptyHint>
            )}
          </div>
        </SectionCard>
        <SectionCard title="Records" subtitle="Records are the persisted source of truth for answer evaluation.">
          <div className="space-y-4">
            {recordsQuery.data?.length ? (
              recordsQuery.data.map((record) => (
                <ResultPanel
                  key={record.id}
                  label={`Record #${record.id}`}
                  content={record.ai_evaluation || record.user_answer}
                  meta={`Score ${record.score ?? 'N/A'} - ${record.created_at}`}
                />
              ))
            ) : (
              <EmptyHint>No interview records yet. Save an answer first to build a traceable history.</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
