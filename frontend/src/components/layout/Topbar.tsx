import { useLocation } from 'react-router-dom'

export interface BreadcrumbItem {
  label: string
  to?: string
}

const PAGE_TITLES: Record<string, string> = {
  '/': '仪表盘',
  '/jobs-explore': '岗位探索',
  '/resume': '简历优化',
  '/interview': '面试准备',
  '/jd-customize': 'JD 定制',
  '/settings/agent-config': 'Agent 配置',
}

export function Topbar({ onCommandPaletteOpen }: { onCommandPaletteOpen?: () => void }) {
  const location = useLocation()
  const pageTitle = PAGE_TITLES[location.pathname] ?? '未知页面'

  return (
    <header className="flex h-14 items-center justify-between border-b border-[var(--color-border)] bg-white px-6">
      {/* Left: Breadcrumb / Page Title */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--color-ink)]">{pageTitle}</span>
        </div>
      </div>

      {/* Right: Keyboard hints */}
      <div className="flex items-center gap-3">
        {/* Command palette trigger */}
        <button
          onClick={onCommandPaletteOpen}
          className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs text-[var(--color-ink-secondary)] transition-colors hover:border-[var(--color-ink-tertiary)] hover:text-[var(--color-ink)]"
        >
          <span>搜索命令...</span>
          <kbd className="ml-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-1.5 py-0.5 font-mono text-[10px]">
            ⌘K
          </kbd>
        </button>
      </div>
    </header>
  )
}
