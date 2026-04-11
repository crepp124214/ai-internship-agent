import { useNavigate } from 'react-router'
import { WorkspaceShell } from './page-primitives'

// 第一层：资源总览面板 - 单一主面板
const OVERVIEW_SUMMARY = '暂无数据。开始添加简历和岗位，以便进入针对性面试练习。'

const LATEST_ACTIVITY = {
  action: '暂无活动记录',
  time: '--',
  icon: '📋',
}

// 辅助资源信息
const RESOURCE_INFO = [
  { label: '简历', value: '0', unit: '份' },
  { label: '岗位', value: '0', unit: '个' },
  { label: '面试记录', value: '0', unit: '次' },
]

// 第二层：三个管理入口 - 半控制台型
const MANAGEMENT_ENTRIES = [
  { label: '简历管理', path: '/settings/resumes', status: '0 份简历', icon: '📄', desc: '管理多版本简历' },
  { label: '岗位管理', path: '/settings/jobs', status: '0 个目标', icon: '💼', desc: '跟踪求职进度' },
  { label: '面试管理', path: '/settings/interviews', status: '0 次练习', icon: '🎤', desc: '查看面试记录' },
]

export function DashboardPage() {
  const navigate = useNavigate()

  return (
    <WorkspaceShell
      title="系统总览"
      subtitle="最近进展感知"
    >
      <div className="min-h-[calc(100vh-12rem)]">
        {/* 第一层：单一资源总览面板 */}
        <div className="mb-10 rounded-3xl border border-[var(--color-border)] bg-gradient-to-br from-slate-50 to-gray-50 p-6 shadow-sm">
          {/* 自动总结 */}
          <p className="mb-4 text-base text-[var(--color-ink-primary)]">{OVERVIEW_SUMMARY}</p>

          {/* 最新活动 */}
          <div className="mb-4 flex items-center gap-3 rounded-xl bg-white/80 px-4 py-3">
            <span className="text-lg">{LATEST_ACTIVITY.icon}</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-[var(--color-ink-primary)]">最新活动：{LATEST_ACTIVITY.action}</p>
              <p className="text-xs text-[var(--color-ink-tertiary)]">{LATEST_ACTIVITY.time}</p>
            </div>
          </div>

          {/* 辅助资源信息 */}
          <div className="flex gap-4 text-xs text-[var(--color-ink-tertiary)]">
            {RESOURCE_INFO.map((info) => (
              <span key={info.label}>
                {info.label}：{info.value}{info.unit}
              </span>
            ))}
          </div>
        </div>

        {/* 第二层：三张管理入口卡 - 半控制台型 */}
        <div className="grid gap-4 sm:grid-cols-3">
          {MANAGEMENT_ENTRIES.map((entry) => (
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
