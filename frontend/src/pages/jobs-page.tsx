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

  return normalized || 'Imported job'
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
      setFeedback('Job created successfully.')
      setJobForm(initialJobForm)
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
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['jobs', 'match-history', selectedJobId] })
      setMatchPreview(`Score ${data.score}\n\n${data.feedback}`)
      setFeedback('Match result saved to history.')
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
        message: `Imported ${file.name}. The title and description were copied into the form.`,
      })
      setFeedback(null)
    } catch {
      setImportStatus({
        kind: 'error',
        message: 'File import failed. Choose a valid txt, md, or json text file.',
      })
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Job Matching Workspace"
        title="Keep target roles and resume evidence on the same desk"
        description="Capture a job, choose a resume, preview the match, and save the result into history."
      />

      <div className="grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
        <SectionCard
          title="Create a Job"
          subtitle="Build a reusable set of demo job records before you compare them with resumes."
        >
          <div className="space-y-4">
            <FormField
              label="Import a local job file"
              helper="Supports txt, md, and json. The file is read in the browser and used to prefill the form."
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
            <FormField label="Job title">
              <Input
                value={jobForm.title}
                onChange={(event) => setJobForm((value) => ({ ...value, title: event.target.value }))}
              />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Company">
                <Input
                  value={jobForm.company}
                  onChange={(event) =>
                    setJobForm((value) => ({ ...value, company: event.target.value }))
                  }
                />
              </FormField>
              <FormField label="Location">
                <Input
                  value={jobForm.location}
                  onChange={(event) =>
                    setJobForm((value) => ({ ...value, location: event.target.value }))
                  }
                />
              </FormField>
            </div>
            <FormField label="Description">
              <Textarea
                value={jobForm.description}
                onChange={(event) =>
                  setJobForm((value) => ({ ...value, description: event.target.value }))
                }
              />
            </FormField>
            <FormField label="Requirements">
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
              Create job
            </PrimaryButton>
          </div>
        </SectionCard>

        <SectionCard
          title="Run a Match"
          subtitle="Pick a job and a resume, preview the result, then decide whether to save it."
        >
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="Job">
              <Select value={selectedJobId ?? ''} onChange={(event) => setSelectedJobId(Number(event.target.value))}>
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id} - {job.title} ({job.company})
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="Resume">
              <Select value={selectedResumeId ?? ''} onChange={(event) => setSelectedResumeId(Number(event.target.value))}>
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} - {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>

          {selectedJob ? (
            <div className="mt-4 rounded-[24px] border border-[var(--color-stroke)] bg-[var(--color-panel)] p-5">
              <p className="text-base font-semibold text-[var(--color-ink)]">{selectedJob.title}</p>
              <p className="mt-1 text-sm text-[var(--color-muted)]">
                {selectedJob.company} - {selectedJob.location}
              </p>
              <p className="mt-4 text-sm leading-7 text-[var(--color-ink)]">{selectedJob.description}</p>
            </div>
          ) : (
            <EmptyHint>Create a job first before you run a match.</EmptyHint>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton
              type="button"
              onClick={() => matchPreviewMutation.mutate()}
              disabled={!selectedJobId || !selectedResumeId}
            >
              Preview match
            </SecondaryButton>
            <PrimaryButton
              type="button"
              onClick={() => persistMatchMutation.mutate()}
              disabled={!selectedJobId || !selectedResumeId}
            >
              Save match history
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
        <SectionCard title="Latest Match Result" subtitle="Preview uses the same backend capability without writing history.">
          {matchPreview ? (
            <ResultPanel label="Match preview" content={matchPreview} />
          ) : (
            <EmptyHint>Preview or save a match result to see output here.</EmptyHint>
          )}
        </SectionCard>
        <SectionCard title="Match History" subtitle="Saved results stay attached to the current job for later review.">
          <div className="space-y-4">
            {matchHistoryQuery.data?.length ? (
              matchHistoryQuery.data.map((item) => (
                <ResultPanel
                  key={item.id}
                  label={`Match #${item.id}`}
                  content={`Score ${item.score}\n\n${item.feedback}`}
                  meta={item.created_at}
                />
              ))
            ) : (
              <EmptyHint>No saved match history yet.</EmptyHint>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
