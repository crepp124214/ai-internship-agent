import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/use-auth'

const navigationItems = [
  { to: '/dashboard', label: '仪表盘' },
  { to: '/resume', label: '简历' },
  { to: '/jobs', label: '岗位' },
  { to: '/interview', label: '面试' },
  { to: '/settings/agent-config', label: 'Agent 配置' },
]

export function AuthenticatedAppShell() {
  const { logout, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-[var(--color-canvas)] text-[var(--color-ink)]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px]">
        <aside className="hidden w-72 flex-col justify-between bg-[var(--color-deep)] px-6 py-8 text-[var(--color-ivory)] lg:flex">
          <div className="space-y-10">
            <div className="space-y-4">
              <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium uppercase tracking-[0.28em] text-white/75">
                作品集展示版
              </div>
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold leading-tight">
                  让每一步求职推进
                  <br />
                  都更清楚
                </h1>
                <p className="max-w-[18rem] text-sm leading-6 text-white/68">
                  让求职准备更清晰高效。
                </p>
              </div>
            </div>

            <nav className="space-y-2">
              {navigationItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      'flex items-center justify-between rounded-2xl px-4 py-3 text-sm transition',
                      isActive
                        ? 'bg-white text-[var(--color-deep)] shadow-[0_18px_40px_rgba(0,0,0,0.18)]'
                        : 'text-white/70 hover:bg-white/8 hover:text-white',
                    ].join(' ')
                  }
                >
                  <span>{item.label}</span>
                  {location.pathname === item.to ? (
                    <span className="rounded-full bg-[var(--color-accent)]/20 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-accent)]">
                      当前
                    </span>
                  ) : null}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="space-y-4 rounded-[28px] border border-white/10 bg-white/6 p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-white">{user?.name ?? user?.username}</p>
              <p className="truncate text-xs text-white/60">{user?.email}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-white/10 px-4 py-3 text-sm font-medium text-white transition hover:bg-white/14"
            >
              退出登录
            </button>
          </div>
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          <header className="border-b border-[var(--color-stroke)]/70 bg-[var(--color-surface)]/80 px-5 py-4 backdrop-blur md:px-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--color-muted)]">
                  AI 求职工作台
                </p>
                <h2 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--color-ink)]">
                  {navigationItems.find((item) => item.to === location.pathname)?.label ?? '仪表盘'}
                </h2>
              </div>
              <div className="flex items-center gap-3 rounded-full border border-[var(--color-stroke)] bg-white px-4 py-2 text-sm text-[var(--color-muted)] shadow-[0_10px_30px_rgba(30,43,40,0.06)]">
                <span className="hidden md:inline">当前登录</span>
                <span className="font-medium text-[var(--color-ink)]">{user?.username}</span>
              </div>
            </div>
          </header>

          <main className="flex-1 px-4 py-5 md:px-8 md:py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
