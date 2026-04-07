// frontend/src/pages/components/TracePanel.tsx
interface TraceStep {
  step: 'planning' | 'tool_call' | 'observation' | 'final'
  content: string
}

interface TracePanelProps {
  steps: TraceStep[]
  open: boolean
  onToggle: () => void
}

const STEP_COLORS: Record<string, string> = {
  planning: 'text-blue-600',
  tool_call: 'text-purple-600',
  observation: 'text-green-600',
  final: 'text-[var(--color-ink)]',
}

const STEP_LABELS: Record<string, string> = {
  planning: '计划',
  tool_call: '工具',
  observation: '观察',
  final: '输出',
}

export function TracePanel({ steps, open, onToggle }: TracePanelProps) {
  return (
    <div className="border-t border-[var(--color-stroke)]">
      {/* 折叠头部 */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-2 text-xs font-medium text-[var(--color-muted)] hover:bg-[var(--color-panel)] transition"
      >
        <span>推理过程 Trace ({steps.length} 步)</span>
        <span>{open ? '▼' : '▲'}</span>
      </button>

      {/* 折叠内容 */}
      {open && (
        <div className="max-h-48 overflow-y-auto bg-[var(--color-canvas)] px-4 pb-3">
          {steps.length === 0 ? (
            <p className="py-2 text-xs text-[var(--color-muted)]">暂无推理步骤</p>
          ) : (
            <div className="space-y-1">
              {steps.map((s, i) => (
                <div key={i} className="flex gap-2 text-xs py-1">
                  <span className={`font-semibold ${STEP_COLORS[s.step] || 'text-gray-600'}`}>
                    [{STEP_LABELS[s.step] || s.step}]
                  </span>
                  <span className="text-[var(--color-ink)] whitespace-pre-wrap">{s.content}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
