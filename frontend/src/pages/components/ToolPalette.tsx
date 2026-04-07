// frontend/src/pages/components/ToolPalette.tsx
import { useState } from 'react'

interface Tool {
  name: string
  description: string
  category: 'resume' | 'job' | 'interview' | 'generic'
}

const TOOLS: Tool[] = [
  { name: 'read_resume', description: '读取简历内容', category: 'resume' },
  { name: 'jd_parser', description: '解析 JD 关键词', category: 'job' },
  { name: 'match_resume_to_job', description: '简历与岗位匹配分析', category: 'job' },
  { name: 'generate_interview_questions', description: '生成面试问题', category: 'interview' },
  { name: 'evaluate_answer', description: '评估回答质量', category: 'interview' },
]

interface ToolPaletteProps {
  onInsertTask: (task: string) => void
}

export function ToolPalette({ onInsertTask }: ToolPaletteProps) {
  const [open, setOpen] = useState(false)

  const byCategory = TOOLS.reduce((acc, tool) => {
    if (!acc[tool.category]) acc[tool.category] = []
    acc[tool.category].push(tool)
    return acc
  }, {} as Record<string, Tool[]>)

  const categoryLabels: Record<string, string> = {
    resume: '简历工具',
    job: '岗位工具',
    interview: '面试工具',
    generic: '通用工具',
  }

  return (
    <>
      {/* 切换按钮 */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed right-4 top-24 z-50 rounded-full bg-[var(--color-surface)] p-3 shadow-lg border border-[var(--color-stroke)] hover:bg-[var(--color-panel)] transition"
        title="工具面板"
      >
        <svg className="w-5 h-5 text-[var(--color-ink)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
        </svg>
      </button>

      {/* 抽屉 */}
      {open && (
        <div className="fixed right-4 top-32 z-50 w-72 rounded-2xl bg-white shadow-xl border border-[var(--color-stroke)] p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--color-ink)]">工具面板</h3>
            <button onClick={() => setOpen(false)} className="text-[var(--color-muted)] hover:text-[var(--color-ink)]">
              ✕
            </button>
          </div>
          <div className="space-y-4">
            {Object.entries(byCategory).map(([cat, tools]) => (
              <div key={cat}>
                <p className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wider mb-2">
                  {categoryLabels[cat] || cat}
                </p>
                <div className="space-y-2">
                  {tools.map(tool => (
                    <button
                      key={tool.name}
                      onClick={() => {
                        onInsertTask(`使用 ${tool.name} 工具：${tool.description}`)
                        setOpen(false)
                      }}
                      className="w-full text-left rounded-xl border border-[var(--color-stroke)] bg-[var(--color-panel)] px-3 py-2 text-sm hover:border-[var(--color-accent)] hover:bg-white transition"
                    >
                      <p className="font-medium text-[var(--color-ink)]">{tool.name}</p>
                      <p className="text-xs text-[var(--color-muted)]">{tool.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
