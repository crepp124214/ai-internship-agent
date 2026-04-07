// frontend/src/pages/components/QuickTaskCard.tsx
interface QuickTaskCardProps {
  title: string
  description: string
  icon: string
  onClick: () => void
}

export function QuickTaskCard({ title, description, icon, onClick }: QuickTaskCardProps) {
  return (
    <button
      onClick={onClick}
      className="group text-left rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-panel)] p-4 transition hover:border-[var(--color-accent)] hover:bg-white hover:shadow-md"
    >
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-accent)]/10 text-xl">
        {icon}
      </div>
      <p className="mb-1 text-sm font-semibold text-[var(--color-ink)] group-hover:text-[var(--color-accent)]">
        {title}
      </p>
      <p className="text-xs text-[var(--color-muted)]">{description}</p>
    </button>
  )
}
