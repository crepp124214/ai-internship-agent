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
  { value: 'applied', label: 'Applied' },
  { value: 'screening', label: 'Screening' },
  { value: 'interview', label: 'Interviewing' },
  { value: 'offer', label: 'Offer received' },
  { value: 'rejected', label: 'Rejected' },
]

type TrackerImportDraft = Partial<{
  job_id: string
  resume_id: string
  status: string
  notes: string
}>

function formatAdviceContent(summary: string, nextSteps: string[], risks: string[]) {
  const nextStepsText = nextSteps.length ? nextSteps.map((step) => `- ${step}`).join('\n') : '- None'
  const risksText = risks.length ? risks.map((risk) => `- ${risk}`).join('\n') : '- None'

  return `${summary}\n\nNext steps\n${nextStepsText}\n\nRisks\n${risksText}`
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
      setImportFeedback(`Imported ${file.name}. The tracker form was updated.`)
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
      setFeedback('Application record created. You can now preview or save AI guidance.')
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
      setFeedback('Tracker advice saved to history.')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Application Tracker"
        title="Keep status, AI guidance, and history on one application timeline"
        description="Link a job and resume, capture the current status, preview next-step advice, and save the recommendation trail."
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard title="Import Tracker Notes" subtitle="Supports local txt, md, and json files and refills the current form.">
          <div className="space-y-4">
            <FormField
              label="Local note file"
              helper="JSON can refill the job, resume, status, and notes. Plain text always fills notes and tries to extract simple fields."
            >
              <Input type="file" accept=".txt,.md,.json" onChange={handleImportFile} />
            </FormField>
            {importFeedback ? (
              <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">
                {importFeedback}
              </div>
            ) : (
              <EmptyHint>Upload a local tracker note to prefill common application fields.</EmptyHint>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Create an Application" subtitle="Tie one job and one resume into a trackable application record.">
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="Job">
              <Select
                value={applicationForm.job_id}
                onChange={(event) => setApplicationForm((value) => ({ ...value, job_id: event.target.value }))}
              >
                <option value="">Select a job</option>
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id} - {job.title}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="Resume">
              <Select
                value={applicationForm.resume_id}
                onChange={(event) => setApplicationForm((value) => ({ ...value, resume_id: event.target.value }))}
              >
                <option value="">Select a resume</option>
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} - {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-[0.42fr_0.58fr]">
            <FormField label="Current status">
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
            <FormField label="Notes">
              <Textarea
                value={applicationForm.notes}
                onChange={(event) => setApplicationForm((value) => ({ ...value, notes: event.target.value }))}
                placeholder="Example: phone screen completed, waiting for recruiter feedback."
              />
            </FormField>
          </div>
          <div className="mt-4">
            <PrimaryButton
              type="button"
              onClick={() => createApplicationMutation.mutate()}
              disabled={!applicationForm.job_id || !applicationForm.resume_id}
            >
              Create application record
            </PrimaryButton>
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="Advice Actions" subtitle="Preview AI guidance first, then decide whether to save it into history.">
          <div className="grid gap-4 md:grid-cols-[0.48fr_0.52fr]">
            <FormField label="Current application">
              <Select
                value={selectedApplicationId ?? ''}
                onChange={(event) => setSelectedApplicationId(Number(event.target.value))}
              >
                <option value="">Select an application</option>
                {applicationsQuery.data?.map((application) => {
                  const statusLabel =
                    defaultStatuses.find((item) => item.value === application.status)?.label ?? application.status

                  return (
                    <option key={application.id} value={application.id}>
                      #{application.id} - Job {application.job_id} - {statusLabel}
                    </option>
                  )
                })}
              </Select>
            </FormField>
            <div className="flex flex-wrap items-end gap-3">
              <SecondaryButton type="button" onClick={() => previewAdviceMutation.mutate()} disabled={!selectedApplicationId}>
                Preview advice
              </SecondaryButton>
              <PrimaryButton type="button" onClick={() => persistAdviceMutation.mutate()} disabled={!selectedApplicationId}>
                Save advice
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
              <ResultPanel label="Advice preview" content={advicePreview} />
            ) : (
              <EmptyHint>Select an application first, then generate advice for it.</EmptyHint>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Application Records" subtitle="Review each application with its linked job, resume, status, and notes.">
          <div className="space-y-4">
            {applicationsQuery.data?.length ? (
              applicationsQuery.data.map((application) => (
                <ResultPanel
                  key={application.id}
                  label={`Application #${application.id}`}
                  content={`Job: ${application.job_id}\nResume: ${application.resume_id}\nStatus: ${
                    defaultStatuses.find((status) => status.value === application.status)?.label ?? application.status
                  }\nNotes: ${application.notes ?? 'No notes yet'}`}
                  meta={application.application_date}
                />
              ))
            ) : (
              <EmptyHint>No application records yet. Create one to start tracking progress.</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Advice History" subtitle="Saved tracker guidance stays here for review and reuse.">
        <div className="space-y-4">
          {adviceHistoryQuery.data?.length ? (
            adviceHistoryQuery.data.map((item) => (
              <ResultPanel
                key={item.id}
                label={`Advice #${item.id}`}
                content={formatAdviceContent(item.summary, item.next_steps, item.risks)}
                meta={item.created_at}
              />
            ))
          ) : (
            <EmptyHint>No advice history yet. Save one recommendation from the panel above to populate this area.</EmptyHint>
          )}
        </div>
      </SectionCard>
    </div>
  )
}
