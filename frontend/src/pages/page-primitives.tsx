import type { ButtonHTMLAttributes, InputHTMLAttributes, PropsWithChildren, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'

/**
 * WorkspaceShell - 统一页面骨架
 * 为 dashboard/jobs/resume/interview/settings 五个核心页面提供统一的页面结构
 * 包含：页面标题区、状态区、动作区、主工作区
 */
export function WorkspaceShell({
  title,
  subtitle,
  statusRail,
  actions,
  children,
}: {
  title: string
  subtitle?: string
  statusRail?: ReactNode
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="workspace-shell">
      <header className="workspace-shell__header flex flex-col gap-4 rounded-[32px] bg-white px-6 py-6 shadow-[0_24px_60px_rgba(30,43,40,0.08)] md:flex-row md:items-end md:justify-between md:px-8">
        <div className="space-y-4">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[var(--color-ink)] md:text-4xl">{title}</h1>
            {subtitle && (
              <p className="max-w-3xl text-sm leading-7 text-[var(--color-muted)] md:text-base">{subtitle}</p>
            )}
          </div>
        </div>
        {actions && <div data-testid="page-actions">{actions}</div>}
      </header>
      {statusRail && (
        <aside data-testid="page-status-rail" className="py-4">
          {statusRail}
        </aside>
      )}
      <main className="workspace-shell__content flex flex-col gap-6">{children}</main>
    </section>
  )
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col gap-4 rounded-[32px] bg-white px-6 py-6 shadow-[0_24px_60px_rgba(30,43,40,0.08)] md:flex-row md:items-end md:justify-between md:px-8">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--color-muted)]">{eyebrow}</p>
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[var(--color-ink)] md:text-4xl">{title}</h1>
          <p className="max-w-3xl text-sm leading-7 text-[var(--color-muted)] md:text-base">{description}</p>
        </div>
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  )
}

export function SectionCard({
  title,
  subtitle,
  children,
  className,
}: PropsWithChildren<{ title: string; subtitle?: string; className?: string }>) {
  return (
    <section className={clsx('rounded-[30px] border border-[var(--color-stroke)] bg-white p-5 shadow-[0_18px_50px_rgba(30,43,40,0.06)] md:p-6', className)}>
      <div className="mb-4 space-y-1">
        <h2 className="text-xl font-semibold tracking-[-0.03em] text-[var(--color-ink)]">{title}</h2>
        {subtitle ? <p className="text-sm leading-6 text-[var(--color-muted)]">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  )
}

export function StatCard({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <div className="rounded-[26px] border border-[var(--color-stroke)] bg-[var(--color-panel)] p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">{label}</p>
      <p className="mt-4 text-3xl font-semibold tracking-[-0.04em] text-[var(--color-ink)]">{value}</p>
      <p className="mt-3 text-sm leading-6 text-[var(--color-muted)]">{helper}</p>
    </div>
  )
}

export function ResultPanel({ label, content, meta }: { label: string; content: string; meta?: string }) {
  return (
    <div className="rounded-[24px] border border-[var(--color-stroke)] bg-[var(--color-surface)] p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-muted)]">{label}</p>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[var(--color-ink)]">{content}</p>
      {meta ? <p className="mt-4 text-xs uppercase tracking-[0.18em] text-[var(--color-muted)]">{meta}</p> : null}
    </div>
  )
}

export function ResultStateNotice({
  tone,
  children,
}: PropsWithChildren<{ tone: 'success' | 'warning' | 'error' }>) {
  const toneClassName =
    tone === 'error'
      ? 'border-[rgba(199,107,79,0.24)] bg-[rgba(199,107,79,0.08)] text-[var(--color-accent)]'
      : tone === 'warning'
        ? 'border-[rgba(190,140,48,0.22)] bg-[rgba(190,140,48,0.1)] text-[rgb(126,89,20)]'
        : 'border-[rgba(86,128,99,0.18)] bg-[rgba(86,128,99,0.1)] text-[rgb(42,102,58)]'

  return (
    <div className={clsx('rounded-[22px] border px-4 py-3 text-sm', toneClassName)}>
      {children}
    </div>
  )
}

export function FormField({ label, children, helper }: PropsWithChildren<{ label: string; helper?: string }>) {
  return (
    <label className="space-y-2">
      <span className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">{label}</span>
      {children}
      {helper ? <span className="block text-xs leading-5 text-[var(--color-muted)]">{helper}</span> : null}
    </label>
  )
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={clsx(
        'w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition placeholder:text-[var(--color-muted)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]',
        props.className,
      )}
    />
  )
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={clsx(
        'min-h-32 w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm leading-7 text-[var(--color-ink)] outline-none transition placeholder:text-[var(--color-muted)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]',
        props.className,
      )}
    />
  )
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={clsx(
        'w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]',
        props.className,
      )}
    />
  )
}

function buttonClasses(base: string, className?: string) {
  return clsx('inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-55', base, className)
}

export function PrimaryButton(props: ButtonHTMLAttributes<HTMLButtonElement> & { to?: never }) {
  return <button {...props} className={buttonClasses('bg-[var(--color-accent)] text-white hover:brightness-95', props.className)} />
}

export function SecondaryButton(props: ButtonHTMLAttributes<HTMLButtonElement> & { to?: never }) {
  return <button {...props} className={buttonClasses('border border-[var(--color-stroke)] bg-white text-[var(--color-ink)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]', props.className)} />
}

export function LinkButton({ to, children }: PropsWithChildren<{ to: string }>) {
  return (
    <Link to={to} className={buttonClasses('bg-[var(--color-accent)] text-white hover:brightness-95')}>
      {children}
    </Link>
  )
}

export function StatusPill({ children }: PropsWithChildren) {
  return (
    <span className="inline-flex items-center rounded-full bg-[rgba(199,107,79,0.14)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-accent)]">
      {children}
    </span>
  )
}

export function EmptyHint({ children }: PropsWithChildren) {
  return (
    <div className="rounded-[24px] border border-dashed border-[var(--color-stroke)] bg-[var(--color-surface)] px-5 py-8 text-sm leading-7 text-[var(--color-muted)]">
      {children}
    </div>
  )
}

/**
 * ResultFrameProps - 统一结果区属性
 */
export type ResultFrameStatus = 'success' | 'fallback' | 'error' | 'loading'

export type ResultFrameProps = {
  status: ResultFrameStatus
  title: string
  /** 标题区补充说明 */
  summary?: ReactNode
  /** 标题区右侧信息 */
  headerMeta?: ReactNode
  /** 自定义状态提示文案 */
  notice?: string
  /** 底部动作区 */
  actions?: ReactNode
  children: ReactNode
}

/**
 * ResultFrame - 统一结果区框架
 * 为 jobs/resume/interview 三个工作区提供统一的 success/fallback/error/loading 四态展示
 * 结构：标题 + 状态提示 + 主体内容 + 下一步动作
 */
export function ResultFrame({ status, title, summary, headerMeta, notice, actions, children }: ResultFrameProps) {
  // 根据状态生成状态提示
  const statusNotice = notice ?? getStatusNotice(status)

  // 状态对应的样式
  const statusStyles = getStatusStyles(status)

  return (
    <section
      data-status={status}
      data-testid="result-frame"
      className="result-frame rounded-[28px] border border-[var(--color-stroke)] bg-white p-5 shadow-[0_18px_50px_rgba(30,43,40,0.06)] md:p-6"
    >
      {/* 标题区 */}
      <div className="mb-4 border-b border-[var(--color-stroke)] pb-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold tracking-[-0.03em] text-[var(--color-ink)]">{title}</h2>
            {summary ? <div className="text-sm leading-6 text-[var(--color-muted)]">{summary}</div> : null}
          </div>
          {headerMeta ? <div className="shrink-0">{headerMeta}</div> : null}
        </div>
      </div>

      {/* 状态提示 - 仅在非 success 状态时显示 */}
      {status !== 'success' && (
        <div className={clsx('mb-4 rounded-[22px] border px-4 py-3 text-sm', statusStyles.notice)}>
          {statusNotice}
        </div>
      )}

      {/* 主体内容 */}
      <div className="result-frame__content space-y-4">{children}</div>

      {/* 底部动作区 */}
      {actions && <div className="mt-4 flex flex-wrap gap-3">{actions}</div>}
    </section>
  )
}

/**
 * 根据状态获取状态提示文案
 */
function getStatusNotice(status: ResultFrameStatus): string {
  switch (status) {
    case 'fallback':
      return '当前显示的是降级结果，不是真实模型输出。'
    case 'error':
      return '操作失败，请重试或稍后再试。'
    case 'loading':
      return '加载中...'
    default:
      return ''
  }
}

/**
 * 根据状态获取样式
 */
function getStatusStyles(status: ResultFrameStatus): { notice: string } {
  switch (status) {
    case 'fallback':
      return {
        notice: 'border-[rgba(190,140,48,0.22)] bg-[rgba(190,140,48,0.1)] text-[rgb(126,89,20)]',
      }
    case 'error':
      return {
        notice: 'border-[rgba(199,107,79,0.24)] bg-[rgba(199,107,79,0.08)] text-[var(--color-accent)]',
      }
    case 'loading':
      return {
        notice: 'border-[rgba(86,128,99,0.18)] bg-[rgba(86,128,99,0.1)] text-[rgb(42,102,58)]',
      }
    default:
      return {
        notice: '',
      }
  }
}
