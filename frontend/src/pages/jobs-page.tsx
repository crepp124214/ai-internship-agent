import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { AgentAssistantPanel } from '../components/agent/AgentAssistantPanel'
import { jobsApi, resumeApi } from '../lib/api'
import {
  PrimaryButton,
  WorkspaceShell,
} from './page-primitives'

// Validate AI response - detect mock/prompt artifacts or invalid content
export function validateAiResponse(content: string | null | undefined): boolean {
  if (!content || typeof content !== 'string') return false
  const trimmed = content.trim()
  if (!trimmed) return false
  
  // Check for specific invalid patterns from mock/downgrade responses
  const invalidPatterns = [
    // Starts with short assessment marker
    /^<short assessment>/i,
    // Contains placeholder fragments like <...>
    /<[^>]*\.\.\.[^>]*>/,
    // Contains pipe-separated raw resume fragments like |姓名：|
    /\|[^\n]+\|[^\n]*$/m,
    // Prompt injection markers
    /^mock-/i,
    /^prompt:/i,
    /^task:/i,
    /^agent/i,
  ]
  
  for (const pattern of invalidPatterns) {
    if (pattern.test(trimmed)) return false
  }
  
  // Check if it's too short or looks like an error
  if (trimmed.length < 10) return false
  
  return true
}

export function JobsPage() {
  const navigate = useNavigate()

  // 原始数据查询
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const selectedJob = useMemo(
    () => jobsQuery.data?.find((job) => job.id === selectedJobId) ?? null,
    [jobsQuery.data, selectedJobId],
  )

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

  const goToResumeOptimize = () => {
    if (!selectedJob) {
      setFeedback('请先选择一个岗位，再执行一键流转。')
      return
    }

    const payload = {
      jobId: selectedJob.id,
      title: selectedJob.title,
      company: selectedJob.company,
      location: selectedJob.location,
      description: selectedJob.description ?? '',
      requirements: selectedJob.requirements ?? '',
    }

    navigate(
      `/resume?fromJob=${selectedJob.id}&targetRole=${encodeURIComponent(`${selectedJob.title}（${selectedJob.company}）`)}&resume_id=${selectedResumeId}`,
      { state: { fromJob: payload } },
    )
  }

  return (
    <WorkspaceShell
      title="岗位工作区"
      subtitle="搜索岗位、分析 JD、匹配简历"
      statusRail={feedback ? <div className="rounded-[22px] bg-[var(--color-panel)] px-4 py-3 text-sm text-[var(--color-ink)]">{feedback}</div> : null}
      actions={
        <PrimaryButton type="button" onClick={goToResumeOptimize} disabled={!selectedJobId}>
          带着岗位去优化简历
        </PrimaryButton>
      }
    >
      <div className="flex h-full flex-col gap-8">
        {/* Agent 助手面板 - 唯一主工作台，内部承载判断、推荐结果和后续动作 */}
        <div className="flex-1" data-testid="agent-assistant-panel">
          <AgentAssistantPanel
            page="job"
            resourceId={selectedJobId ?? undefined}
            resourceIds={selectedResumeId ? [selectedResumeId] : []}
            quickActions={[
              { label: '🔍 搜索岗位', message: '帮我搜索公司招聘官网' },
              { label: '分析 JD', message: '请分析这个岗位的 JD 要求' },
              { label: '与简历匹配', message: '这个岗位和我的简历匹配吗？' },
            ]}
          />
        </div>
      </div>
    </WorkspaceShell>
  )
}
