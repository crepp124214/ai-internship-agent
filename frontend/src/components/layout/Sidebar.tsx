import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../../auth/use-auth'

export interface NavItem {
  to: string
  label: string
  icon: string
  keywords?: string[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: '仪表盘', icon: '◉', keywords: ['dashboard', '首页', 'home'] },
  { to: '/jobs-explore', label: '岗位探索', icon: '◈', keywords: ['jobs', '岗位', 'job'] },
  { to: '/resume', label: '简历优化', icon: '◇', keywords: ['resume', '简历', 'cv'] },
  { to: '/interview', label: '面试准备', icon: '◎', keywords: ['interview', '面试'] },
  { to: '/settings/agent-config', label: 'Agent 配置', icon: '⚙', keywords: ['agent', 'config', '设置', '配置'] },
]

export function Sidebar() {
  const location = useLocation()
  const { user } = useAuth()

  return (
    <aside className="flex w-60 flex-col bg-[#0D0D0D]">
      {/* Logo / Brand */}
      <div className="flex h-14 items-center border-b border-white/8 px-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-white/10 text-xs text-white/80">
            ◈
          </div>
          <span className="text-sm font-medium text-white">AI 求职工作台</span>
        </div>
      </div>

      {/* Navigation */}
      <nav aria-label="主导航" className="flex-1 overflow-y-auto px-2 py-3">
        <div className="mb-2 px-2 py-1.5">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-white/30">
            导航
          </span>
        </div>
        <ul className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.to
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={[
                    'group relative flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-colors',
                    isActive
                      ? 'bg-white text-black'
                      : 'text-white/60 hover:bg-white/8 hover:text-white',
                  ].join(' ')}
                >
                  {/* Left indicator bar (only for active) */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-[var(--color-accent)]" />
                  )}
                  <span className="text-base">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                  {/* Keyboard hint when active */}
                  {isActive && (
                    <span className="ml-auto hidden text-[10px] text-black/40 group-hover:hidden">
                      ⌘{item.to === '/' ? 'D' : item.to === '/jobs-explore' ? 'J' : item.to === '/resume' ? 'R' : item.to === '/interview' ? 'I' : 'S'}
                    </span>
                  )}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer / User info */}
      <div className="border-t border-white/8 px-3 py-4">
        <div className="flex items-center gap-2.5 rounded-lg px-2 py-2 hover:bg-white/8">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-xs text-white/80">
            {user?.name?.[0] ?? user?.username?.[0] ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-white">{user?.name ?? user?.username}</p>
            <p className="truncate text-xs text-white/40">{user?.email}</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

export { NAV_ITEMS }
