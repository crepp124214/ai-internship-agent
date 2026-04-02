import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { interviewApi, jobsApi, resumeApi, trackerApi } from '../lib/api'
import { EmptyHint, LinkButton, PageHeader, ResultPanel, SectionCard, StatCard, StatusPill } from './page-primitives'

function cleanMockText(value: string | null | undefined, fallback: string) {
  if (!value) {
    return fallback
  }

  const collapsed = value.replace(/^mock-generate:/, '').replace(/\s+/g, ' ').trim()

  if (!collapsed) {
    return fallback
  }

  const scoreMatch = collapsed.match(/Score:\s*([0-9]{1,3})/i)
  const feedbackMatch = collapsed.match(/Feedback:\s*(.+)$/i)

  if (feedbackMatch?.[1]) {
    return feedbackMatch[1].trim()
  }

  if (collapsed.includes('<short assessment>')) {
    return '这块已经有保存过的 AI 结果，可以前往对应工作区继续查看。'
  }

  if (collapsed.includes('<one concise paragraph>')) {
    return '这条投递已经有保存过的跟进建议，可以在投递追踪里继续查看。'
  }

  if (collapsed.startsWith('# ') || collapsed.includes('Task:')) {
    return fallback
  }

  const firstSentence = collapsed.split(/(?<=[.!?])\s+/)[0]?.trim()
  const candidate = firstSentence && firstSentence.length > 18 ? firstSentence : collapsed.slice(0, 180).trim()

  if (scoreMatch?.[1] && candidate) {
    return `${candidate} (Score ${scoreMatch[1]})`
  }

  return candidate || fallback
}

export function DashboardPage() {
  const resumesQuery = useQuery({ queryKey: ['resume', 'list'], queryFn: resumeApi.list })
  const jobsQuery = useQuery({ queryKey: ['jobs', 'list'], queryFn: jobsApi.list })
  const interviewRecordsQuery = useQuery({ queryKey: ['interview', 'records'], queryFn: interviewApi.listRecords })
  const applicationsQuery = useQuery({ queryKey: ['tracker', 'applications'], queryFn: trackerApi.listApplications })

  const latestResume = resumesQuery.data?.[0] ?? null
  const latestJob = jobsQuery.data?.[0] ?? null
  const latestApplication = applicationsQuery.data?.[0] ?? null
  const latestRecord = interviewRecordsQuery.data?.[0] ?? null

  const summaryHistoryQuery = useQuery({
    queryKey: ['resume', 'summary-history', latestResume?.id],
    queryFn: () => resumeApi.getSummaryHistory(latestResume!.id),
    enabled: Boolean(latestResume),
  })

  const jobMatchHistoryQuery = useQuery({
    queryKey: ['jobs', 'match-history', latestJob?.id],
    queryFn: () => jobsApi.getMatchHistory(latestJob!.id),
    enabled: Boolean(latestJob),
  })

  const adviceHistoryQuery = useQuery({
    queryKey: ['tracker', 'advice-history', latestApplication?.id],
    queryFn: () => trackerApi.getAdviceHistory(latestApplication!.id),
    enabled: Boolean(latestApplication),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="AI 求职工作台"
        title="让每一步求职推进都更清楚"
        description="你的简历、岗位匹配、面试准备和投递建议都在这里统一查看。"
        action={<LinkButton to="/resume">进入简历中心</LinkButton>}
      />

      <div className="grid gap-4 xl:grid-cols-4">
        <StatCard label="简历状态" value={String(resumesQuery.data?.length ?? 0)} helper="当前可用于摘要、优化和岗位匹配的简历数量。" />
        <StatCard label="岗位匹配" value={String(jobsQuery.data?.length ?? 0)} helper="已录入并可用于匹配与投递追踪的岗位数量。" />
        <StatCard label="面试准备" value={String(interviewRecordsQuery.data?.length ?? 0)} helper="已经沉淀下来的面试回答与评估记录数量。" />
        <StatCard label="投递追踪" value={String(applicationsQuery.data?.length ?? 0)} helper="已经建立并可继续跟进的投递记录数量。" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <SectionCard title="最新 AI 输出" subtitle="这里展示的是已经生成或保存过的结果，不会凭空拼接不存在的数据。">
          <div className="grid gap-4 md:grid-cols-2">
            {summaryHistoryQuery.data?.[0] ? (
              <ResultPanel
                label="简历摘要"
                content={cleanMockText(summaryHistoryQuery.data[0].optimized_text, '已经保存过简历摘要，可以前往简历工作区继续查看。')}
                meta={`模型来源：${summaryHistoryQuery.data[0].provider ?? '未知'}`}
              />
            ) : (
              <EmptyHint>暂时还没有保存过的简历摘要。先去简历页生成并保存一次摘要吧。</EmptyHint>
            )}

            {jobMatchHistoryQuery.data?.[0] ? (
              <ResultPanel
                label="岗位匹配"
                content={cleanMockText(jobMatchHistoryQuery.data[0].feedback, '已经保存过岗位匹配结果，可以前往岗位工作区继续查看。')}
                meta={`匹配分数：${jobMatchHistoryQuery.data[0].score}`}
              />
            ) : (
              <EmptyHint>暂时还没有保存过的岗位匹配结果。先在岗位页完成一次匹配并保存吧。</EmptyHint>
            )}

            {latestRecord?.ai_evaluation ? (
              <ResultPanel
                label="面试评估"
                content={cleanMockText(latestRecord.ai_evaluation, '已经保存过面试评估，可以前往面试工作区继续查看。')}
                meta={`评估分数：${latestRecord.score ?? '暂无'}`}
              />
            ) : (
              <EmptyHint>暂时还没有保存过的面试评估。先在面试页记录并评分一次回答吧。</EmptyHint>
            )}

            {adviceHistoryQuery.data?.[0] ? (
              <ResultPanel
                label="投递建议"
                content={cleanMockText(adviceHistoryQuery.data[0].summary, '已经保存过投递建议，可以前往投递追踪工作区继续查看。')}
                meta={`下一步建议数：${adviceHistoryQuery.data[0].next_steps.length}`}
              />
            ) : (
              <EmptyHint>暂时还没有保存过的投递建议。先在投递追踪页生成并保存一次建议吧。</EmptyHint>
            )}
          </div>
        </SectionCard>

        <SectionCard title="快捷操作" subtitle="按下面的顺序补齐数据，就可以走完一条完整的演示链路。">
          <div className="space-y-3">
            {[
              ['/resume', '简历', '创建简历并编辑内容，生成摘要与优化建议。'],
              ['/jobs', '岗位', '录入岗位并选择简历，生成并保存匹配结果。'],
              ['/interview', '面试', '生成题目、记录回答，并保存评估结果。'],
              ['/tracker', '投递追踪', '创建投递记录，生成并保存下一步建议。'],
            ].map(([to, title, description]) => (
              <Link
                key={title}
                to={to}
                className="block rounded-[24px] border border-[var(--color-stroke)] bg-[var(--color-panel)] p-4 transition hover:border-[var(--color-accent)] hover:bg-white"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <p className="text-base font-semibold text-[var(--color-ink)]">{title}</p>
                    <StatusPill>可用</StatusPill>
                  </div>
                  <p className="text-sm leading-6 text-[var(--color-muted)]">{description}</p>
                </div>
              </Link>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
