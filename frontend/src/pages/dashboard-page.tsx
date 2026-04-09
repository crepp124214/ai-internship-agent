import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AgentChatPanel } from './components/AgentChatPanel'
import { DataImportModal } from './components/DataImportModal'

  // Demo 数据 — 暖色渐变风格
  // 注意：以下数据为演示用 mock 数据，实际使用时会从后端 API 获取真实数据
  // 演示模式下展示功能入口，用户创建数据后会自动显示真实统计
  const DEMO_STATS = [
    { label: '简历', value: '→', icon: '📄', gradient: 'from-rose-50 to-orange-50' },
    { label: '岗位', value: '→', icon: '💼', gradient: 'from-violet-50 to-purple-50' },
    { label: '面试', value: '→', icon: '🎤', gradient: 'from-cyan-50 to-blue-50' },
  ]

  const DEMO_RECENT = [
    { type: '简历', action: '优化建议已保存', time: '10:30', icon: '📄' },
    { type: '匹配', action: '与字节跳动岗位匹配成功', time: '昨天', icon: '💼' },
    { type: '面试', action: '完成 AI 模拟面试', time: '3天前', icon: '🎤' },
  ]

export function DashboardPage() {
  const navigate = useNavigate()
  const [showImportModal, setShowImportModal] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)

  return (
    <div className="relative min-h-[calc(100vh-12rem)]">
      {/* 统计卡片区 — 暖色渐变卡片 */}
      <div className="mb-10 grid gap-5 sm:grid-cols-3">
        {DEMO_STATS.map((stat) => (
          <button
            key={stat.label}
            onClick={() => navigate(stat.label === '简历' ? '/resume' : stat.label === '岗位' ? '/jobs-explore' : '/interview')}
            className={`group relative overflow-hidden rounded-3xl border border-[var(--color-border)] bg-gradient-to-br ${stat.gradient} p-6 text-left shadow-[var(--shadow-card)] transition-all hover:-translate-y-1 hover:shadow-lg`}
          >
            {/* 装饰圆形 */}
            <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/40 opacity-0 transition-opacity group-hover:opacity-100" />

            <div className="mb-4 flex items-center justify-between">
              <span className="text-3xl">{stat.icon}</span>
              <span className="text-xs font-medium text-[var(--color-ink-tertiary)] opacity-0 transition-opacity group-hover:opacity-100">
                →
              </span>
            </div>
            <p className={`font-bold tracking-tight text-[var(--color-ink-primary)] ${stat.value === '→' ? 'text-2xl' : 'text-4xl'}`}>{stat.value}</p>
            <p className="mt-1 text-sm text-[var(--color-ink-secondary)]">{stat.label}</p>
          </button>
        ))}
      </div>

      {/* 最近活动 */}
      <div className="mb-10">
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink-primary)]">最近活动</h2>
        <div className="space-y-3">
          {DEMO_RECENT.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-4 rounded-2xl border border-[var(--color-border)] bg-white/80 px-5 py-4 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:shadow-md"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-rose-100 to-orange-100 text-lg">
                {item.icon}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[var(--color-ink-primary)]">{item.action}</p>
                <p className="text-xs text-[var(--color-ink-tertiary)]">{item.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 右下角 AI 按钮 */}
      <button
        onClick={() => setAiOpen(!aiOpen)}
        className="fixed bottom-8 right-8 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-secondary)] text-xl text-white shadow-lg transition-all hover:scale-110 hover:shadow-xl"
      >
        {aiOpen ? '×' : '🤖'}
      </button>

      {/* AI 助手面板 */}
      {aiOpen && (
        <div className="fixed bottom-24 right-8 w-96 rounded-3xl border border-[var(--color-border)] bg-white shadow-2xl">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] px-5 py-4">
            <h3 className="font-semibold text-[var(--color-ink-primary)]">AI 求职助手</h3>
            <button onClick={() => setAiOpen(false)} className="text-2xl text-[var(--color-ink-tertiary)] hover:text-[var(--color-ink-primary)]">
              ×
            </button>
          </div>
          <div className="h-80">
            <AgentChatPanel initialTask="" />
          </div>
        </div>
      )}

      {/* 数据导入弹窗 */}
      <DataImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImportSuccess={() => setShowImportModal(false)}
      />
    </div>
  )
}
