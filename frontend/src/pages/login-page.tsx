import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/use-auth'
import { FormField, Input, PrimaryButton } from './page-primitives'

export function LoginPage() {
  const { isAuthenticated, isBootstrapping, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('demo123')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isBootstrapping && isAuthenticated) {
    const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/dashboard'
    return <Navigate replace to={destination} />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      await login(username, password)
      navigate('/dashboard', { replace: true })
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '登录失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--color-canvas)] px-4 py-8 text-[var(--color-ink)] md:px-8 md:py-10">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-[1540px] overflow-hidden rounded-[40px] bg-white shadow-[0_30px_90px_rgba(30,43,40,0.08)] lg:grid-cols-[1.15fr_0.85fr]">
        <section className="relative overflow-hidden bg-[var(--color-deep)] px-8 py-10 text-[var(--color-ivory)] md:px-12 md:py-14">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(199,107,79,0.34),transparent_38%),radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.08),transparent_28%)]" />
          <div className="relative flex h-full flex-col justify-between">
            <div className="space-y-6">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/70">求职作品集</p>
              <div className="space-y-5">
                <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-[-0.05em] md:text-6xl">
                  AI 实习求职工作台
                </h1>
                <p className="max-w-xl text-base leading-8 text-white/75 md:text-lg">
                  登录后即可查看简历状态、岗位匹配、面试准备和投递建议，把求职推进收进一个清晰的工作区。
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center bg-[var(--color-surface)] px-6 py-10 md:px-10">
          <div className="mx-auto w-full max-w-md space-y-8">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--color-muted)]">作品集展示版</p>
              <h2 className="text-3xl font-semibold tracking-[-0.04em] text-[var(--color-ink)]">开始你的下一段求职推进</h2>
              <p className="text-sm leading-7 text-[var(--color-muted)]">
                当前版本为作品集展示版，核心展示后端能力与产品工作流。请使用已创建账号登录，或先在后端创建测试账号。
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <FormField label="用户名">
                <Input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="请输入用户名" />
              </FormField>
              <FormField label="密码">
                <Input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="请输入密码"
                />
              </FormField>

              {errorMessage ? (
                <div className="rounded-[24px] border border-[rgba(199,107,79,0.35)] bg-[rgba(199,107,79,0.08)] px-4 py-3 text-sm leading-6 text-[var(--color-accent)]">
                  {errorMessage}
                </div>
              ) : null}

              <PrimaryButton type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? '登录中...' : '登录'}
              </PrimaryButton>
            </form>
          </div>
        </section>
      </div>
    </div>
  )
}
