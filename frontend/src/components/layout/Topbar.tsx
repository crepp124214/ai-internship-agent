import { useLocation, Link } from 'react-router-dom'

const PAGE_TITLES: Record<string, string> = {
  '/': '仪表盘',
  '/jobs-explore': '岗位探索',
  '/resume': '简历优化',
  '/interview': '面试准备',
  '/jd-customize': 'JD 定制',
  '/settings': '设置中心',
  '/settings/resumes': '简历管理',
  '/settings/jobs': '岗位管理',
  '/settings/interviews': '面试记录',
  '/settings/agent-config': 'Agent 配置',
}

const SETTINGS_SUB_PATHS = ['/settings/resumes', '/settings/jobs', '/settings/interviews', '/settings/agent-config']

export function Topbar() {
  const location = useLocation()
  const pageTitle = PAGE_TITLES[location.pathname] ?? '未知页面'
  const isSettingsSubPage = SETTINGS_SUB_PATHS.includes(location.pathname)

  return (
    <header className="flex h-14 items-center border-b border-[var(--color-border)] bg-white/80 backdrop-blur-sm px-6">
      {isSettingsSubPage ? (
        <div className="flex items-center gap-3">
          <Link
            to="/settings"
            className="flex items-center gap-1 text-sm text-[var(--color-ink-tertiary)] transition-colors hover:text-[var(--color-ink-primary)]"
          >
            <span>←</span>
            <span>设置中心</span>
          </Link>
          <span className="text-[var(--color-ink-tertiary)]">/</span>
          <span className="text-sm font-medium text-[var(--color-ink-primary)]">{pageTitle}</span>
        </div>
      ) : (
        <span className="text-sm font-medium text-[var(--color-ink-secondary)]">{pageTitle}</span>
      )}
    </header>
  )
}
