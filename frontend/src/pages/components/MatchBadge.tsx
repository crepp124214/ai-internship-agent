// frontend/src/pages/components/MatchBadge.tsx
import { clsx } from 'clsx'

interface MatchBadgeProps {
  score: number // 0-100
  showBar?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function MatchBadge({ score, showBar = true, size = 'md' }: MatchBadgeProps) {
  const percent = Math.round(score)
  const isHigh = percent >= 80
  const isMedium = percent >= 60 && percent < 80

  const colorClass = isHigh
    ? 'text-[var(--color-success)]'
    : isMedium
      ? 'text-[var(--color-warning)]'
      : 'text-[var(--color-error)]'

  const barClass = isHigh
    ? 'bg-[var(--color-success)]'
    : isMedium
      ? 'bg-[var(--color-warning)]'
      : 'bg-[var(--color-error)]'

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  }

  return (
    <div className="flex items-center gap-2">
      <span
        className={clsx(
          'inline-flex items-center justify-center rounded-full font-semibold tabular-nums',
          colorClass,
          sizeClasses[size],
        )}
      >
        {percent}%
      </span>
      {showBar && (
        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-[var(--color-border)]">
          <div
            className={clsx('h-full rounded-full transition-all', barClass)}
            style={{ width: `${percent}%` }}
          />
        </div>
      )}
    </div>
  )
}
