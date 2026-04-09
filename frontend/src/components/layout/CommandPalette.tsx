import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

export interface Command {
  id: string
  label: string
  description?: string
  icon?: string
  keywords?: string[]
  action: () => void
  category?: string
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

const COMMANDS: Command[] = [
  {
    id: 'nav-dashboard',
    label: '仪表盘',
    description: '查看首页仪表盘',
    icon: '◉',
    keywords: ['dashboard', '首页', 'home'],
    action: () => navigate('/'),
    category: '导航',
  },
  {
    id: 'nav-jobs',
    label: '岗位探索',
    description: '浏览和搜索岗位',
    icon: '◈',
    keywords: ['jobs', '岗位', 'job', 'explore'],
    action: () => navigate('/jobs-explore'),
    category: '导航',
  },
  {
    id: 'nav-resume',
    label: '简历优化',
    description: '管理和优化简历',
    icon: '◇',
    keywords: ['resume', '简历', 'cv'],
    action: () => navigate('/resume'),
    category: '导航',
  },
  {
    id: 'nav-interview',
    label: '面试准备',
    description: 'AI 模拟面试练习',
    icon: '◎',
    keywords: ['interview', '面试'],
    action: () => navigate('/interview'),
    category: '导航',
  },
  {
    id: 'nav-agent-config',
    label: 'Agent 配置',
    description: '配置 AI Agent 设置',
    icon: '⚙',
    keywords: ['agent', 'config', 'settings', '配置'],
    action: () => navigate('/settings/agent-config'),
    category: '设置',
  },
]

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const filteredCommands = useMemo(() => COMMANDS.filter((cmd) => {
    if (!query) return true
    const q = query.toLowerCase()
    return (
      cmd.label.toLowerCase().includes(q) ||
      cmd.keywords?.some((k) => k.toLowerCase().includes(q))
    )
  }), [query])

  // Reset state when opening
  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [isOpen])

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex((i) => Math.max(i - 1, 0))
          break
        case 'Enter':
          e.preventDefault()
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action()
            onClose()
          }
          break
        case 'Escape':
          e.preventDefault()
          onClose()
          break
      }
    },
    [filteredCommands, selectedIndex, onClose]
  )

  if (!isOpen) return null

  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Palette */}
      <div className="relative w-full max-w-lg rounded-2xl border border-[var(--color-border)] bg-white shadow-2xl">
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-[var(--color-border)] px-4 py-3">
          <span className="text-lg text-[var(--color-ink-secondary)]">⌘</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            onKeyDown={handleKeyDown}
            placeholder="搜索命令..."
            aria-label="搜索命令"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--color-ink-tertiary)]"
          />
          <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-ink-secondary)]">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div role="listbox" className="max-h-80 overflow-y-auto py-2">
          {filteredCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-[var(--color-ink-tertiary)]">
              未找到匹配的命令
            </div>
          ) : (
            filteredCommands.map((cmd, index) => (
              <button
                key={cmd.id}
                role="option"
                onClick={() => {
                  cmd.action()
                  onClose()
                }}
                onMouseEnter={() => setSelectedIndex(index)}
                className={[
                  'flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors',
                  index === selectedIndex
                    ? 'bg-[var(--color-accent)] text-white'
                    : 'hover:bg-[var(--color-surface-hover)]',
                ].join(' ')}
              >
                <span className="text-base">{cmd.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${index === selectedIndex ? 'text-white' : 'text-[var(--color-ink)]'}`}>
                    {cmd.label}
                  </p>
                  {cmd.description && (
                    <p className={`text-xs ${index === selectedIndex ? 'text-white/70' : 'text-[var(--color-ink-secondary)]'}`}>
                      {cmd.description}
                    </p>
                  )}
                </div>
                {cmd.category && (
                  <span className={`text-[10px] ${index === selectedIndex ? 'text-white/50' : 'text-[var(--color-ink-tertiary)]'}`}>
                    {cmd.category}
                  </span>
                )}
                {index === selectedIndex && (
                  <kbd className="rounded border border-white/20 bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-white/70">
                    ↵
                  </kbd>
                )}
              </button>
            ))
          )}
        </div>

        {/* Footer hints */}
        <div className="flex items-center justify-between border-t border-[var(--color-border)] px-4 py-2 text-[10px] text-[var(--color-ink-tertiary)]">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1 py-0.5 font-mono">
                ↑
              </kbd>
              <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1 py-0.5 font-mono">
                ↓
              </kbd>
              导航
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1 py-0.5 font-mono">
                ↵
              </kbd>
              选择
            </span>
          </div>
          <div className="flex items-center gap-1">
            <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1 py-0.5 font-mono">
              G
            </kbd>
            <span>+</span>
            <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1 py-0.5 font-mono">
              D/J/R/I
            </kbd>
            <span>跳转</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export { COMMANDS }
