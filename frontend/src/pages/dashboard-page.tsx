import { useNavigate } from 'react-router'
import { WorkspaceShell } from './page-primitives'

// 系统总览数据 - 系统总览型 + 半控制台入口
const SYSTEM_STATS = [
  { label: '简历库', value: '0', unit: '份', path: '/settings/resumes', icon: '📄', gradient: 'from-rose-50 to-orange-50', desc: '管理多版本简历' },
  { label: '目标岗位', value: '0', unit: '个', path: '/settings/jobs', icon: '💼', gradient: 'from-violet-50 to-purple-50', desc: '跟踪求职进度' },
  { label: '面试练习', value: '0', unit: '次', path: '/settings/interviews', icon: '🎤', gradient: 'from-cyan-50 to-blue-50', desc: 'AI 模拟面试' },
  { label: '申请跟踪', value: '0', unit: '个', path: '/jobs', icon: '📋', gradient: 'from-emerald-50 to-teal-50', desc: '投递状态追踪' },
]

// 控制台入口 - 半控制台风格
const CONSOLE_ENTRIES = [
  { label: '求职 Agent', icon: '🤖', path: '/jobs', desc: 'AI 岗位推荐与匹配' },
  { label: '简历优化', icon: '✏️', path: '/resume', desc: 'AI 简历分析与优化' },
  { label: '面试教练', icon: '🎯', path: '/interview', desc: 'AI 模拟面试' },
  { label: '申请追踪', icon: '📊', path: '/jobs', desc: '投递进度管理' },
]

export function DashboardPage() {
  const navigate = useNavigate()

  return (
    <WorkspaceShell
      title="系统总览"
      subtitle="一站式求职管理系统"
    >
      <div className="min-h-[calc(100vh-12rem)]">
        {/* 系统状态区 — Professional 风格卡片 */}
        <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SYSTEM_STATS.map((stat) => (
            <button
              key={stat.label}
              onClick={() => navigate(stat.path)}
              className={`group relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-gradient-to-br ${stat.gradient} p-5 text-left shadow-sm transition-all hover:shadow-md hover:border-[var(--color-accent)]/30`}
            >
              {/* 装饰圆形 */}
              <div className="absolute -right-6 -top-6 h-28 w-28 rounded-full bg-white/30" />

              <div className="mb-3 flex items-center justify-between">
                <span className="text-2xl">{stat.icon}</span>
                <span className="text-xs text-[var(--color-ink-tertiary)] transition-transform group-hover:translate-x-1">→</span>
              </div>
              <p className="font-bold tracking-tight text-[var(--color-ink-primary)] text-3xl">
                {stat.value}<span className="ml-1 text-sm font-normal text-[var(--color-ink-tertiary)]">{stat.unit}</span>
              </p>
              <p className="mt-1 text-sm font-medium text-[var(--color-ink-secondary)]">{stat.label}</p>
              <p className="mt-0.5 text-xs text-[var(--color-ink-tertiary)]">{stat.desc}</p>
            </button>
          ))}
        </div>

        {/* 控制台入口区 — 半控制台风格 */}
        <div className="mb-10">
          <h2 className="mb-4 text-base font-semibold text-[var(--color-ink-primary)]">快速入口</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {CONSOLE_ENTRIES.map((entry) => (
              <button
                key={entry.label}
                onClick={() => navigate(entry.path)}
                className="group flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-white/80 px-4 py-3 text-left shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md hover:border-[var(--color-accent)]/30"
              >
                <span className="text-xl">{entry.icon}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-[var(--color-ink-primary)]">{entry.label}</p>
                  <p className="text-xs text-[var(--color-ink-tertiary)]">{entry.desc}</p>
                </div>
                <span className="text-lg text-[var(--color-ink-tertiary)] transition-transform group-hover:translate-x-1">→</span>
              </button>
            ))}
          </div>
        </div>

        {/* 状态说明 */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-gray-50/50 px-5 py-4">
          <p className="text-xs text-[var(--color-ink-tertiary)]">
            💡 当前为演示模��，数据将从后端获取后自动更新。点击上方卡片或入口进入对应管理页面。
          </p>
        </div>
      </div>
    </WorkspaceShell>
  )
}
