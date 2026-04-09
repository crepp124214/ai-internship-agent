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
      className="group text-left rounded-[var(--radius-xl)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-all duration-[var(--duration-fast)] hover:border-[var(--color-accent)] hover:bg-[var(--color-surface)] hover:shadow-[var(--shadow-lg)] hover:-translate-y-1"
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-accent-subtle)] text-2xl transition-transform duration-[var(--duration-fast)] group-hover:scale-110">
        {icon}
      </div>
      <p className="font-body mb-2 text-base font-semibold text-[var(--color-ink)] transition-colors duration-[var(--duration-fast)] group-hover:text-[var(--color-accent)]">
        {title}
      </p>
      <p className="font-body text-sm text-[var(--color-ink-muted)] leading-[var(--leading-relaxed)]">{description}</p>
    </button>
  )
}
