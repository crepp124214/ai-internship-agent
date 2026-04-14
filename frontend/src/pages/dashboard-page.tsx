import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { WorkspaceShell } from './page-primitives'
import { interviewApi, jobsApi, resumeApi, type InterviewQuestionSet, type InterviewSession } from '../lib/api'

// 默认兜底数据
const DEFAULT_SUMMARY = '暂无数据。开始添加简历和岗位，以便进入针对性面试练习。'
const DEFAULT_ACTIVITY = { action: '暂无活动记录', time: '--', icon: '📋' }

/**
 * 生成自动总结文案（规则驱动，不依赖 AI）
 */
function generateSummary(data: {
  hasResume: boolean
  hasJob: boolean
  hasQuestionSet: boolean
  hasCompletedSession: boolean
}): string {
  const { hasResume, hasJob, hasQuestionSet, hasCompletedSession } = data

  // 最高优先级：有完成面试
  if (hasCompletedSession) {
    return '你最近完成了一轮面试练习。下一步建议根据反馈继续优化。'
  }
  // 次优先级：有题集
  if (hasQuestionSet) {
    return '你已经准备好面试材料。下一步建议开始一轮模拟面试。'
  }
  // 次优先级：有岗位
  if (hasJob) {
    return '你已经进入岗位筛选阶段。下一步建议生成一组面试题。'
  }
  // 次优先级：有简历
  if (hasResume) {
    return '你已经完成简历准备。下一步建议先补充目标岗位。'
  }
  // 兜底：全部为空
  return DEFAULT_SUMMARY
}

/**
 * 生成最新活动文案（规则驱动）
 */
function generateLatestActivity(data: {
  latestQuestionSet: InterviewQuestionSet | null
  latestCompletedSession: InterviewSession | null
  latestJob: { title: string; created_at: string } | null
  latestResume: { title: string; created_at: string } | null
}): { action: string; time: string; icon: string } {
  const { latestQuestionSet, latestCompletedSession, latestJob, latestResume } = data

  // 优先级：题集 > 完成面试 > 岗位 > 简历
  if (latestQuestionSet) {
    const time = new Date(latestQuestionSet.created_at).toLocaleDateString('zh-CN')
    return { action: `保存了"${latestQuestionSet.title}"`, time, icon: '📚' }
  }

  if (latestCompletedSession) {
    const time = new Date(latestCompletedSession.created_at).toLocaleDateString('zh-CN')
    return { action: '完成了一次技术面试练习', time, icon: '🎤' }
  }

  if (latestJob) {
    const time = new Date(latestJob.created_at).toLocaleDateString('zh-CN')
    return { action: `新增了目标岗位"${latestJob.title}"`, time, icon: '💼' }
  }

  if (latestResume) {
    const time = new Date(latestResume.created_at).toLocaleDateString('zh-CN')
    return { action: `导入了简历"${latestResume.title}"`, time, icon: '📄' }
  }

  return DEFAULT_ACTIVITY
}

export function DashboardPage() {
  const navigate = useNavigate()

  // 并行查询四个数据源，局部失败不阻塞整页
  const resumesQuery = useQuery({
    queryKey: ['dashboard', 'resumes'],
    queryFn: resumeApi.list,
  })

  const jobsQuery = useQuery({
    queryKey: ['dashboard', 'jobs'],
    queryFn: jobsApi.list,
  })

  const sessionsQuery = useQuery({
    queryKey: ['dashboard', 'sessions'],
    queryFn: interviewApi.listSessions,
  })

  const questionSetsQuery = useQuery({
    queryKey: ['dashboard', 'questionSets'],
    queryFn: interviewApi.listQuestionSets,
  })

  // 安全获取数据（允许部分失败）
  const resumes = resumesQuery.data ?? []
  const jobs = jobsQuery.data ?? []
  const sessions = sessionsQuery.data ?? []
  const questionSets = questionSetsQuery.data ?? []

  // 计算资源数量
  const resumeCount = resumes.length
  const jobCount = jobs.length
  const sessionCount = sessions.length
  const questionSetCount = questionSets.length

  // 统计默认简历数
  const defaultResumeCount = resumes.filter((r) => r.is_default).length
  // 统计进行中岗位数
  const activeJobCount = jobs.filter((j) => j.is_active).length
  // 统计已完成面试数（completed = 1 表示完成）
  const completedSessionCount = sessions.filter((s) => s.completed === 1).length

  // 生成自动总结（使用已成功获取的数据）
  const summary = generateSummary({
    hasResume: resumeCount > 0,
    hasJob: jobCount > 0,
    hasQuestionSet: questionSetCount > 0,
    hasCompletedSession: completedSessionCount > 0,
  })

  // 获取最新关键成果
  const latestQuestionSet = questionSets.length > 0 ? questionSets[0] : null
  const latestCompletedSession = sessions.length > 0 ? sessions.find((s) => s.completed === 1) ?? null : null
  const latestJob = jobs.length > 0 ? { title: jobs[0].title, created_at: jobs[0].created_at } : null
  const latestResume = resumes.length > 0 ? { title: resumes[0].title, created_at: resumes[0].created_at } : null

  const latestActivity = generateLatestActivity({
    latestQuestionSet,
    latestCompletedSession,
    latestJob,
    latestResume,
  })

  // 管理入口卡数据
  const managementEntries = [
    {
      label: '简历管理',
      path: '/settings/resumes',
      status: `${resumeCount} 份简历${defaultResumeCount > 0 ? `，${defaultResumeCount} 份默认` : ''}`,
      icon: '📄',
      desc: '管理多版本简历',
    },
    {
      label: '岗位管理',
      path: '/settings/jobs',
      status: `${jobCount} 个目标${activeJobCount > 0 ? `，${activeJobCount} 个进行中` : ''}`,
      icon: '💼',
      desc: '跟踪求职进度',
    },
    {
      label: '面试管理',
      path: '/settings/interviews',
      status: `${sessionCount} 次练习${questionSetCount > 0 ? `，${questionSetCount} 个题集` : ''}`,
      icon: '🎤',
      desc: '查看面试记录',
    },
  ]

  return (
    <WorkspaceShell
      title="系统总览"
      subtitle="最近进展感知"
    >
      <div className="min-h-[calc(100vh-12rem)]">
        {/* 第一层：资源总览面板 */}
        <div className="mb-10 rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
          {/* 自动总结 */}
          <p className="mb-4 text-base text-[var(--color-ink-primary)]">{summary}</p>

          {/* 最新活动 */}
          <div className="mb-4 flex items-center gap-3 rounded-xl bg-white/80 px-4 py-3">
            <span className="text-lg">{latestActivity.icon}</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-[var(--color-ink-primary)]">最新活动：{latestActivity.action}</p>
              <p className="text-xs text-[var(--color-ink-tertiary)]">{latestActivity.time}</p>
            </div>
          </div>

          {/* 辅助资源信息 */}
          <div className="flex gap-4 text-xs text-[var(--color-ink-tertiary)]">
            <span>简历：{resumeCount}份</span>
            <span>岗位：{jobCount}个</span>
            <span>面试记录：{sessionCount}次</span>
          </div>
        </div>

        {/* 第二层：三张管理入口卡 - 半控制台型 */}
        <div className="grid gap-4 sm:grid-cols-3">
          {managementEntries.map((entry) => (
            <button
              key={entry.label}
              onClick={() => navigate(entry.path)}
              className="group flex items-center gap-4 rounded-2xl border border-[var(--color-border)] bg-white/80 px-5 py-4 text-left shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md hover:border-[var(--color-accent)]/30"
            >
              <span className="text-2xl">{entry.icon}</span>
              <div className="flex-1">
                <p className="text-sm font-medium text-[var(--color-ink-primary)]">{entry.label}</p>
                <p className="text-xs text-[var(--color-ink-tertiary)]">{entry.status}</p>
                <p className="mt-0.5 text-xs text-[var(--color-ink-secondary)]">{entry.desc}</p>
              </div>
              <span className="text-lg text-[var(--color-ink-tertiary)] transition-transform group-hover:translate-x-1">→</span>
            </button>
          ))}
        </div>
      </div>
    </WorkspaceShell>
  )
}