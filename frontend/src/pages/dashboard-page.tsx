import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AgentChatPanel } from './components/AgentChatPanel'
import { DataImportModal } from './components/DataImportModal'

// Demo 数据
const DEMO_STATS = [
  { label: '简历', value: 3, icon: '📄', color: '#c76b4f' },
  { label: '岗位', value: 5, icon: '💼', color: '#5b8a72' },
  { label: '面试', value: 2, icon: '🎤', color: '#6b7fd4' },
]

const DEMO_RECENT = [
  { type: '简历', action: '优化建议已保存', time: '10:30' },
  { type: '匹配', action: '与字节跳动岗位匹配成功', time: '昨天' },
  { type: '面试', action: '完成 AI 模拟面试', time: '3天前' },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const [showImportModal, setShowImportModal] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)

  return (
    <div className="relative min-h-[calc(100vh-12rem)]">
      {/* 统计卡片区 */}
      <div className="mb-10 grid gap-6 sm:grid-cols-3">
        {DEMO_STATS.map((stat) => (
          <button
            key={stat.label}
            onClick={() => navigate(stat.label === '简历' ? '/resume' : stat.label === '岗位' ? '/jobs-explore' : '/interview')}
            className="group rounded-[28px] border border-[var(--color-border)] bg-white p-6 text-left shadow-[0_8px_32px_rgba(30,43,40,0.06)] transition-all hover:-translate-y-1 hover:shadow-[0_16px_48px_rgba(30,43,40,0.1)]"
          >
            <div className="mb-4 flex items-center justify-between">
              <span className="text-3xl">{stat.icon}</span>
              <span className="text-xs font-medium uppercase tracking-widest text-[var(--color-ink-muted)] opacity-0 transition-opacity group-hover:opacity-100">
                查看 →
              </span>
            </div>
            <p className="text-4xl font-semibold tracking-tight text-[var(--color-ink)]">{stat.value}</p>
            <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{stat.label}</p>
          </button>
        ))}
      </div>

      {/* 最近活动 */}
      <div className="mb-10">
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink)]">最近活动</h2>
        <div className="space-y-3">
          {DEMO_RECENT.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-4 rounded-2xl border border-[var(--color-border)] bg-white px-5 py-4 shadow-sm"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface)] text-lg">
                {item.type === '简历' ? '📄' : item.type === '匹配' ? '💼' : '🎤'}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[var(--color-ink)]">{item.action}</p>
                <p className="text-xs text-[var(--color-ink-muted)]">{item.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 快捷入口 */}
      <div className="mb-10">
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink)]">快捷入口</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/resume')}
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-white px-5 py-3 text-sm font-medium text-[var(--color-ink)] shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            📄 管理简历
          </button>
          <button
            onClick={() => navigate('/jobs-explore')}
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-white px-5 py-3 text-sm font-medium text-[var(--color-ink)] shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            💼 岗位探索
          </button>
          <button
            onClick={() => navigate('/interview')}
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-white px-5 py-3 text-sm font-medium text-[var(--color-ink)] shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            🎤 开始面试
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-white px-5 py-3 text-sm font-medium text-[var(--color-ink)] shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            + 导入数据
          </button>
        </div>
      </div>

      {/* 右下角 AI 按钮 */}
      <button
        onClick={() => setAiOpen(!aiOpen)}
        className="fixed bottom-8 right-8 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-accent)] text-xl text-white shadow-lg transition-all hover:scale-110 hover:shadow-xl"
      >
        {aiOpen ? '×' : '🤖'}
      </button>

      {/* AI 助手面板 */}
      {aiOpen && (
        <div className="fixed bottom-24 right-8 w-96 rounded-3xl border border-[var(--color-border)] bg-white shadow-2xl">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] px-5 py-4">
            <h3 className="font-semibold text-[var(--color-ink)]">AI 求职助手</h3>
            <button onClick={() => setAiOpen(false)} className="text-2xl text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]">
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
