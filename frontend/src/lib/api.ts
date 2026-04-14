import axios from 'axios'

import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from '../auth/auth-storage'
import type { AuthUser } from '../auth/use-auth'

export type TokenResponse = {
  access_token: string
  token_type: string
}

export type LoginPayload = {
  username: string
  password: string
}

export type Resume = {
  id: number
  user_id: number
  title: string
  original_file_path: string
  file_name: string
  file_type: string
  file_size: number | null
  processed_content: string | null
  resume_text: string | null
  language: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export type ResumeCreatePayload = {
  title: string
  file_path: string
}

export type ResumeUpdatePayload = Partial<{
  title: string
  processed_content: string | null
  resume_text: string | null
  language: string
  is_default: boolean
}>

export type ResumeAnalysisPayload = {
  target_role?: string | null
}

export type ResumeAnalysisResponse = {
  mode: 'summary' | 'improvements'
  resume_id: number
  target_role: string | null
  content: string
  raw_content: string | null
  provider: string | null
  model: string | null
  status?: 'success' | 'fallback'
  fallback_used?: boolean | null
}

export type ResumeOptimization = {
  id: number
  resume_id: number
  original_text: string
  optimized_text: string
  optimization_type: string
  keywords: string | null
  score: number | null
  ai_suggestion: string | null
  mode: 'resume_summary' | 'resume_improvements'
  raw_content: string
  provider: string
  model: string
  created_at: string
  updated_at: string
}

export type MatchReportData = {
  keyword_coverage: number
  match_score: number
  gaps: string[]
  suggestions: string[]
}

export type ResumeCustomizeResponse = {
  customized_resume: string
  match_report: MatchReportData | null
  session_id: string
}

export type Job = {
  id: number
  title: string
  company: string
  location: string
  description: string
  requirements: string | null
  company_logo: string | null
  salary: string | null
  work_type: string | null
  experience: string | null
  education: string | null
  welfare: string | null
  tags: string | null
  source: string
  source_url: string | null
  source_id: string | null
  is_active: boolean
  publish_date: string | null
  deadline: string | null
  created_at: string
  updated_at: string
}

/**
 * 推荐岗位结构（Task 2 主入口）
 */
export type RecommendedJob = {
  id: number
  title: string
  company: string
  location?: string
  workType?: string
  tags?: string[]
  recommendationScore: number
  officialUrl?: string
  summary?: string
}

type RecommendedJobApiResponse = {
  id: number
  title: string
  company: string
  location?: string
  work_type?: string | null
  tags?: string[] | null
  recommendation_score: number
  official_url?: string | null
  summary?: string | null
}

export type JobCreatePayload = {
  title: string
  company: string
  location: string
  description: string
  requirements?: string | null
  salary?: string | null
  work_type?: string | null
  experience?: string | null
  education?: string | null
  welfare?: string | null
  tags?: string | null
  source: string
  source_url?: string | null
  source_id?: string | null
}

export type JobSaveExternalPayload = {
  title: string
  company: string
  location: string
  description: string
  requirements?: string | null
  source_url?: string | null
}

export type JobUpdatePayload = {
  title?: string
  company?: string
  location?: string
  description?: string
  requirements?: string | null
  salary?: string | null
  work_type?: string | null
  experience?: string | null
  education?: string | null
  welfare?: string | null
  tags?: string | null
  source?: string
  source_url?: string | null
  source_id?: string | null
  is_active?: boolean
}

export type JobMatchPayload = {
  resume_id: number
}

export type JobMatchResponse = {
  mode: 'job_match'
  job_id: number
  resume_id: number
  score: number
  feedback: string
  raw_content: string | null
  provider: string | null
  model: string | null
  status?: 'success' | 'fallback'
  fallback_used?: boolean | null
}

export type JobMatchRecord = {
  id: number
  job_id: number
  resume_id: number
  mode: 'job_match'
  score: number
  feedback: string
  raw_content: string
  provider: string
  model: string
  created_at: string
  updated_at: string
}

export type InterviewQuestion = {
  id: number
  question_type: string
  difficulty: string
  question_text: string
  category: string
  tags: string | null
  sample_answer: string | null
  reference_material: string | null
  created_at: string
  updated_at: string
}

export type InterviewQuestionCreatePayload = {
  question_type: string
  difficulty?: string | null
  question_text: string
  category?: string | null
  tags?: string | null
  sample_answer?: string | null
  reference_material?: string | null
}

export type InterviewQuestionGenerationPayload = {
  job_context: string
  resume_id?: number | null
  count: number
}

export type GeneratedInterviewQuestion = {
  question_number: number
  question_text: string
  question_type: string
  difficulty: string
  category: string
}

export type ReviewReport = {
  dimensions: Array<{ name: string; score: number; stars: number; suggestion: string }>
  overall_score: number
  overall_comment: string
  improvement_suggestions: string[]
  markdown: string
}

export type InterviewQuestionGenerationResponse = {
  mode: 'question_generation'
  job_context: string
  resume_context: string | null
  count: number
  questions: GeneratedInterviewQuestion[]
  raw_content: string
  provider: string | null
  model: string | null
  status?: 'success' | 'fallback'
  fallback_used?: boolean | null
}

export type InterviewAnswerEvaluationPayload = {
  question_text: string
  user_answer: string
  job_context?: string | null
}

export type InterviewAnswerEvaluationResponse = {
  mode: 'answer_evaluation'
  question_text: string
  user_answer: string
  job_context: string | null
  score: number
  feedback: string
  raw_content: string
  provider: string | null
  model: string | null
}

export type InterviewSession = {
  id: number
  user_id: number
  job_id: number | null
  session_type: string
  duration: number | null
  total_questions: number | null
  average_score: number | null
  completed: number | null
  created_at: string
  updated_at: string
}

export type InterviewSessionCreatePayload = {
  job_id?: number | null
  session_type: string
  duration?: number | null
  total_questions?: number | null
  average_score?: number | null
  completed?: number | null
}

export type InterviewRecord = {
  id: number
  user_id: number
  job_id: number | null
  question_id: number
  user_answer: string
  ai_evaluation: string | null
  score: number | null
  feedback: string | null
  provider: string | null
  model: string | null
  created_at: string
  updated_at: string
}

export type InterviewRecordCreatePayload = {
  job_id?: number | null
  question_id: number
  user_answer: string
}

export type InterviewRecordEvaluationPayload = {
  job_context?: string | null
}

export type InterviewRecordEvaluationResponse = {
  mode: 'answer_evaluation'
  record_id: number
  score: number
  feedback: string
  ai_evaluation: string
  raw_content: string
  provider: string | null
  model: string | null
  answered_at: string
}

export type ApplicationTracker = {
  id: number
  user_id: number
  job_id: number
  resume_id: number
  status: string
  notes: string | null
  application_date: string
  status_updated_at: string
  created_at: string
  updated_at: string
}

export type ApplicationTrackerCreatePayload = {
  job_id: number
  resume_id: number
  status: string
  notes?: string | null
}

export type ApplicationAdviceResponse = {
  mode: 'tracker_advice'
  application_id: number
  summary: string
  next_steps: string[]
  risks: string[]
  raw_content: string | null
  provider: string | null
  model: string | null
}

export type TrackerAdviceRecord = {
  id: number
  application_id: number
  mode: 'tracker_advice'
  summary: string
  next_steps: string[]
  risks: string[]
  raw_content: string | null
  provider: string | null
  model: string | null
  created_at: string
  updated_at: string
}

type RefreshDecision = {
  status?: number
  requestUrl?: string
  retryAttempted?: boolean
}

const apiBaseUrl = (function() {
  // In development, use relative path to go through Vite proxy
  if (import.meta.env.DEV) {
    return ''  // Relative URL - goes through Vite proxy to http://127.0.0.1:8000
  }
  // In production, use configured base URL
  return (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')
})()

const api = axios.create({
  baseURL: `${apiBaseUrl}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

let refreshTokenRequest: Promise<string | null> | null = null

export function shouldAttemptTokenRefresh({
  status,
  requestUrl,
  retryAttempted,
}: RefreshDecision): boolean {
  if (status !== 401 || retryAttempted) {
    return false
  }

  const normalizedUrl = requestUrl ?? ''
  return !normalizedUrl.includes('/auth/refresh')
}

async function requestTokenRefresh(): Promise<string | null> {
  if (!refreshTokenRequest) {
    refreshTokenRequest = api
      .post<TokenResponse>('/auth/refresh')
      .then((response) => response.data.access_token ?? null)
      .finally(() => {
        refreshTokenRequest = null
      })
  }

  return refreshTokenRequest
}

api.interceptors.request.use((config) => {
  const token = getStoredToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as (typeof error.config & { _retry?: boolean }) | undefined

    if (
      originalRequest &&
      shouldAttemptTokenRefresh({
        status: error.response?.status,
        requestUrl: originalRequest.url,
        retryAttempted: originalRequest._retry,
      })
    ) {
      originalRequest._retry = true
      try {
        const access_token = await requestTokenRefresh()
        if (access_token) {
          setStoredToken(access_token)
          originalRequest.headers = {
            ...originalRequest.headers,
            Authorization: `Bearer ${access_token}`,
          }
          return api(originalRequest)
        }
      } catch {
        clearStoredToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export function readApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return '请求失败，请稍后重试。'
}

export const authApi = {
  async login(payload: LoginPayload) {
    const response = await api.post<TokenResponse>('/auth/login', payload)
    return response.data
  },
  async refreshToken() {
    const response = await api.post<TokenResponse>('/auth/refresh')
    return response.data
  },
  async logout() {
    const response = await api.post('/auth/logout')
    return response.data
  },
  async getCurrentUser() {
    const response = await api.get<AuthUser>('/users/me')
    return response.data
  },
}

export const resumeApi = {
  async list() {
    const response = await api.get<Resume[]>('/resumes/')
    return response.data
  },
  async create(payload: ResumeCreatePayload) {
    const response = await api.post<Resume>('/resumes/', payload)
    return response.data
  },
  async update(resumeId: number, payload: ResumeUpdatePayload) {
    const response = await api.put<Resume>(`/resumes/${resumeId}`, payload)
    return response.data
  },
  async previewSummary(resumeId: number, payload: ResumeAnalysisPayload) {
    const response = await api.post<ResumeAnalysisResponse>(`/resumes/${resumeId}/summary/`, payload)
    return response.data
  },
  async persistSummary(resumeId: number, payload: ResumeAnalysisPayload) {
    const response = await api.post<ResumeOptimization>(`/resumes/${resumeId}/summary/persist/`, payload)
    return response.data
  },
  async getSummaryHistory(resumeId: number) {
    const response = await api.get<ResumeOptimization[]>(`/resumes/${resumeId}/summary/history/`)
    return response.data
  },
  async previewImprovements(resumeId: number, payload: ResumeAnalysisPayload) {
    const response = await api.post<ResumeAnalysisResponse>(`/resumes/${resumeId}/improvements/`, payload)
    return response.data
  },
  async persistImprovements(resumeId: number, payload: ResumeAnalysisPayload) {
    const response = await api.post<ResumeOptimization>(`/resumes/${resumeId}/improvements/persist/`, payload)
    return response.data
  },
  async getOptimizationHistory(resumeId: number) {
    const response = await api.get<ResumeOptimization[]>(`/resumes/${resumeId}/optimizations/`)
    return response.data
  },
  async customizeForJd(resumeId: number, jdId: number, customInstructions?: string) {
    const response = await api.post<ResumeCustomizeResponse>(`/resumes/${resumeId}/customize-for-jd`, {
      jd_id: jdId,
      custom_instructions: customInstructions,
      enable_match_report: true,
    })
    return response.data
  },
  async delete(resumeId: number) {
    await api.delete(`/resumes/${resumeId}`)
  },
}

export const jobsApi = {
  async list() {
    const response = await api.get<Job[]>('/jobs/')
    return response.data
  },
  async getById(jobId: number) {
    const response = await api.get<Job>(`/jobs/${jobId}`)
    return response.data
  },
  async create(payload: JobCreatePayload) {
    const response = await api.post<Job>('/jobs/', payload)
    return response.data
  },
  async update(jobId: number, payload: JobUpdatePayload) {
    const response = await api.put<Job>(`/jobs/${jobId}`, payload)
    return response.data
  },
  async delete(jobId: number) {
    await api.delete(`/jobs/${jobId}`)
  },
  async saveExternal(payload: JobSaveExternalPayload) {
    const response = await api.post<Job>('/jobs/save-external', payload)
    return response.data
  },
  async previewMatch(jobId: number, payload: JobMatchPayload) {
    const response = await api.post<JobMatchResponse>(`/jobs/${jobId}/match/`, payload)
    return response.data
  },
  async persistMatch(jobId: number, payload: JobMatchPayload) {
    const response = await api.post<JobMatchRecord>(`/jobs/${jobId}/match/persist/`, payload)
    return response.data
  },
  async getMatchHistory(jobId: number) {
    const response = await api.get<JobMatchRecord[]>(`/jobs/${jobId}/match-history/`)
    return response.data
  },
  /**
   * 获取推荐岗位（Task 2 主入口）
   * 根据求职目标摘要返回 5 条推荐岗位
   */
  async getRecommendedJobs(goalSummary: string) {
    const response = await api.get<RecommendedJobApiResponse[]>('/jobs/recommended/', {
      params: { goal_summary: goalSummary },
    })
    return response.data.map((job) => ({
      id: job.id,
      title: job.title,
      company: job.company,
      location: job.location,
      workType: job.work_type ?? undefined,
      tags: job.tags ?? [],
      recommendationScore: job.recommendation_score,
      officialUrl: job.official_url ?? undefined,
      summary: job.summary ?? undefined,
    }))
  },
}

export type InterviewQuestionSet = {
  id: number
  user_id: number
  title: string
  job_id: number | null
  resume_id: number | null
  source: string
  status: string
  questions: GeneratedInterviewQuestion[]
  created_at: string
  updated_at: string
}

export type InterviewQuestionSetCreatePayload = {
  title: string
  job_id?: number | null
  resume_id?: number | null
  source?: string
  status?: string
  questions: GeneratedInterviewQuestion[]
}

export type InterviewQuestionSetUpdatePayload = {
  title?: string
  status?: string
}

export const interviewApi = {
  async listQuestions() {
    const response = await api.get<InterviewQuestion[]>('/interview/questions/')
    return response.data
  },
  async createQuestion(payload: InterviewQuestionCreatePayload) {
    const response = await api.post<InterviewQuestion>('/interview/questions/', payload)
    return response.data
  },
  async generateQuestions(payload: InterviewQuestionGenerationPayload) {
    const response = await api.post<InterviewQuestionGenerationResponse>('/interview/questions/generate/', payload)
    return response.data
  },
  async evaluateAnswer(payload: InterviewAnswerEvaluationPayload) {
    const response = await api.post<InterviewAnswerEvaluationResponse>('/interview/answers/evaluate/', payload)
    return response.data
  },
  async listSessions() {
    const response = await api.get<InterviewSession[]>('/interview/sessions/')
    return response.data
  },
  async createSession(payload: InterviewSessionCreatePayload) {
    const response = await api.post<InterviewSession>('/interview/sessions/', payload)
    return response.data
  },
  async listQuestionSets() {
    const response = await api.get<InterviewQuestionSet[]>('/interview/question-sets')
    return response.data
  },
  async createQuestionSet(payload: InterviewQuestionSetCreatePayload) {
    const response = await api.post<InterviewQuestionSet>('/interview/question-sets', payload)
    return response.data
  },
  async updateQuestionSet(questionSetId: number, payload: InterviewQuestionSetUpdatePayload) {
    const response = await api.patch<InterviewQuestionSet>(`/interview/question-sets/${questionSetId}`, payload)
    return response.data
  },
  async deleteQuestionSet(questionSetId: number) {
    await api.delete(`/interview/question-sets/${questionSetId}`)
  },
  async startCoachFromQuestionSet(questionSetId: number) {
    const response = await api.post(`/interview/question-sets/${questionSetId}/start-coach`)
    return response.data
  },
  async listRecords() {
    const response = await api.get<InterviewRecord[]>('/interview/records/')
    return response.data
  },
  async createRecord(payload: InterviewRecordCreatePayload) {
    const response = await api.post<InterviewRecord>('/interview/records/', payload)
    return response.data
  },
  async evaluateRecord(recordId: number, payload: InterviewRecordEvaluationPayload) {
    const response = await api.post<InterviewRecordEvaluationResponse>(
      `/interview/records/${recordId}/evaluate/`,
      payload,
    )
    return response.data
  },
  async coachStart(payload: { jd_id: number; resume_id: number; question_count?: number }) {
    const response = await api.post('/interview/coach/start', payload)
    return response.data
  },
  async coachAnswer(payload: { session_id: number; answer: string }) {
    const response = await api.post('/interview/coach/answer', payload)
    return response.data
  },
  async coachFollowup(payload: { session_id: number; followup_answers: Array<{ question: string; answer: string }> }) {
    const response = await api.post('/interview/coach/followup', payload)
    return response.data
  },
  async coachEnd(sessionId: number, followupSkipped: boolean = false) {
    const response = await api.post('/interview/coach/end', null, { params: { session_id: sessionId, followup_skipped: followupSkipped } })
    return response.data
  },
  async coachGetReport(sessionId: number) {
    const response = await api.get<{ session_id: number; review_report: ReviewReport; average_score: number }>(`/interview/coach/report/${sessionId}`)
    return response.data
  },
}

export const trackerApi = {
  async listApplications() {
    const response = await api.get<ApplicationTracker[]>('/tracker/applications/')
    return response.data
  },
  async createApplication(payload: ApplicationTrackerCreatePayload) {
    const response = await api.post<ApplicationTracker>('/tracker/applications/', payload)
    return response.data
  },
  async previewAdvice(applicationId: number) {
    const response = await api.post<ApplicationAdviceResponse>(`/tracker/applications/${applicationId}/advice/`)
    return response.data
  },
  async persistAdvice(applicationId: number) {
    const response = await api.post<TrackerAdviceRecord>(`/tracker/applications/${applicationId}/advice/persist/`)
    return response.data
  },
  async getAdviceHistory(applicationId: number) {
    const response = await api.get<TrackerAdviceRecord[]>(
      `/tracker/applications/${applicationId}/advice-history/`,
    )
    return response.data
  },
}

// User LLM Config types and functions
export interface UserLlmConfig {
  agent: string
  provider: string
  model: string
  api_key: string | null
  base_url: string | null
  temperature: number
  is_active: boolean
  updated_at: string
}

export interface UserLlmConfigInput {
  agent: string
  provider: string
  model: string
  api_key: string
  base_url?: string | null
  temperature?: number
}

export async function getUserLlmConfigs(): Promise<UserLlmConfig[]> {
  const response = await api.get<UserLlmConfig[]>('/users/llm-configs/')
  return response.data
}

export async function saveUserLlmConfig(data: UserLlmConfigInput): Promise<UserLlmConfig> {
  const response = await api.post<UserLlmConfig>('/users/llm-configs/', data)
  return response.data
}

export async function deleteUserLlmConfig(agent: string): Promise<void> {
  await api.delete(`/users/llm-configs/${agent}`)
}

// Test LLM Config types and response
export interface TestLlmConfigRequest {
  provider: string
  model: string
  api_key: string
  base_url?: string | null
}

export interface TestLlmConfigResponse {
  status: 'success' | 'error'
  provider: string
  model: string
  latency_ms: number
  fallback_used: boolean
  error_code: string | null
  error_message: string | null
  agent?: string
}

export async function testGlobalLlmConfig(input: TestLlmConfigRequest): Promise<TestLlmConfigResponse> {
  const response = await api.post<TestLlmConfigResponse>('/users/llm-configs/test', input)
  return response.data
}

export async function testAgentLlmConfig(agent: string, input: TestLlmConfigRequest): Promise<TestLlmConfigResponse> {
  const response = await api.post<TestLlmConfigResponse>(`/users/llm-configs/test-agent`, { agent, ...input })
  return response.data
}

export interface AgentTool {
  name: string
  description: string
  category: string
}

export async function getAgentTools(): Promise<AgentTool[]> {
  const response = await api.get<{ tools: AgentTool[] }>('/agent/tools/')
  return response.data.tools
}
