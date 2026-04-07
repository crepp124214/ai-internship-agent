import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AgentChatPanel } from './components/AgentChatPanel'
import { ToolPalette } from './components/ToolPalette'
import { TracePanel } from './components/TracePanel'
import { QuickTaskCard } from './components/QuickTaskCard'

interface TraceStep {
  step: 'planning' | 'tool_call' | 'observation' | 'final'
  content: string
}

const QUICK_TASKS = [
  {
    title: 'JD 定制简历',
    description: '根据岗位定制优化简历',
    icon: '📄',
    task: '帮我根据这个岗位定制简历',
  },
  {
    title: '面试对练',
    description: 'AI 面试官多轮练习',
    icon: '🎤',
    task: '我想进行面试练习',
  },
  {
    title: '岗位推荐',
    description: '根据简历推荐合适岗位',
    icon: '💼',
    task: '帮我推荐一些合适的岗位',
  },
  {
    title: '投递建议',
    description: '分析投递进度与下一步',
    icon: '📋',
    task: '给我的投递一些建议',
  },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const [selectedTask, setSelectedTask] = useState<string | null>(null)
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([])
  const [traceOpen, setTraceOpen] = useState(false)

  const handleQuickTask = (task: string) => {
    setSelectedTask(task)
  }

  const handleBackToDashboard = () => {
    setSelectedTask(null)
    setTraceSteps([])
  }

  // Agent Workspace 模式
  if (selectedTask) {
    return (
      <div className="flex h-[calc(100vh-8rem)] flex-col rounded-3xl border border-[var(--color-stroke)] bg-white shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--color-stroke)] px-5 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={handleBackToDashboard}
              className="rounded-lg border border-[var(--color-stroke)] px-3 py-1.5 text-sm hover:bg-[var(--color-panel)] transition"
            >
              ← 返回
            </button>
            <h2 className="text-sm font-semibold text-[var(--color-ink)]">AI 求职助手</h2>
          </div>
          <button
            onClick={() => setTraceOpen(!traceOpen)}
            className={`rounded-lg border px-3 py-1.5 text-xs transition ${
              traceOpen ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-accent)]' : 'border-[var(--color-stroke)] text-[var(--color-muted)] hover:bg-[var(--color-panel)]'
            }`}
          >
            Trace {traceSteps.length > 0 ? `(${traceSteps.length})` : ''}
          </button>
        </div>

        {/* Trace Panel */}
        <TracePanel
          steps={traceSteps}
          open={traceOpen}
          onToggle={() => setTraceOpen(!traceOpen)}
        />

        {/* Chat Panel */}
        <div className="flex-1 overflow-hidden">
          <AgentChatPanel initialTask={selectedTask} />
        </div>

        {/* Tool Palette */}
        <ToolPalette onInsertTask={(t) => setSelectedTask(t)} />
      </div>
    )
  }

  // 默认仪表盘模式
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--color-muted)]">
            AI 求职工作台
          </p>
          <h1 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--color-ink)]">
            让每一步求职推进都更清楚
          </h1>
        </div>
        <button
          onClick={() => navigate('/resume')}
          className="rounded-full bg-[var(--color-accent)] px-5 py-2.5 text-sm font-medium text-white transition hover:opacity-90"
        >
          进入简历中心
        </button>
      </div>

      {/* 快捷任务区 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {QUICK_TASKS.map((qt) => (
          <QuickTaskCard
            key={qt.title}
            title={qt.title}
            description={qt.description}
            icon={qt.icon}
            onClick={() => handleQuickTask(qt.task)}
          />
        ))}
      </div>

      {/* 提示区 */}
      <div className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-panel)] p-6 text-center">
        <p className="text-sm text-[var(--color-muted)]">
          点击上方快捷任务卡片，或直接输入任何求职问题
        </p>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          AI 将根据你的上下文自动调用合适的工具处理
        </p>
      </div>
    </div>
  )
}