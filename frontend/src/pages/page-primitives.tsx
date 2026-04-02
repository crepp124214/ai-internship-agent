import type { ButtonHTMLAttributes, InputHTMLAttributes, PropsWithChildren, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'

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
      <div className="mb-5 space-y-1">
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
