import { useNavigate } from 'react-router-dom'

const SETTINGS_CARDS = [
    {
      id: 'resumes',
      icon: '📄',
      title: '简历管理',
      description: '上传、编辑和管理简历',
      stats: '点击查看',
      gradient: 'from-rose-50 to-orange-50',
      path: '/settings/resumes',
    },
    {
      id: 'jobs',
      icon: '💼',
      title: '岗位管理',
      description: '导入和管理目标岗位',
      stats: '点击查看',
      gradient: 'from-violet-50 to-purple-50',
      path: '/settings/jobs',
    },
    {
      id: 'interviews',
      icon: '🎤',
      title: '面试记录',
      description: '查看练习历史和报告',
      stats: '点击查看',
      gradient: 'from-cyan-50 to-blue-50',
      path: '/settings/interviews',
    },
    {
      id: 'agent',
      icon: '🤖',
      title: 'Agent 配置',
      description: '配置 LLM Provider 和模型',
      stats: '点击配置',
      gradient: 'from-emerald-50 to-teal-50',
      path: '/settings/agent-config',
    },
  ]

export function SettingsPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-ink-primary)]">设置中心</h1>
        <p className="mt-1 text-sm text-[var(--color-ink-tertiary)]">管理你的简历、岗位和 AI 配置</p>
      </div>

      {/* Card Grid — Notion style */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4">
        {SETTINGS_CARDS.map((card) => (
          <button
            key={card.id}
            onClick={() => navigate(card.path)}
            className={`group relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-gradient-to-br ${card.gradient} p-6 text-left shadow-[var(--shadow-card)] transition-all hover:-translate-y-1 hover:shadow-lg`}
          >
            {/* Decorative circle */}
            <div className="absolute -right-6 -top-6 h-28 w-28 rounded-full bg-white/30 opacity-0 transition-opacity group-hover:opacity-100" />

            {/* Icon */}
            <div className="mb-4 text-4xl">{card.icon}</div>

            {/* Title */}
            <h3 className="mb-1 text-base font-semibold text-[var(--color-ink-primary)]">{card.title}</h3>

            {/* Description */}
            <p className="mb-4 text-xs text-[var(--color-ink-tertiary)]">{card.description}</p>

            {/* Stats */}
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--color-ink-secondary)]">{card.stats}</span>
              <span className="text-xs font-medium text-[var(--color-accent)] opacity-0 transition-opacity group-hover:opacity-100">
                →
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
