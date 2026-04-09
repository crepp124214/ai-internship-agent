// frontend/src/pages/components/DiffContent.tsx
import { diffWords } from 'diff'

interface DiffContentProps {
  original: string
  modified: string
}

interface DiffPart {
  value: string
  added?: boolean
  removed?: boolean
}

export function DiffContent({ original, modified }: DiffContentProps) {
  const parts: DiffPart[] = diffWords(original, modified)

  let addedCount = 0
  let removedCount = 0

  parts.forEach((part) => {
    if (part.added) {
      addedCount += part.value.split(/\s+/).filter(Boolean).length
    } else if (part.removed) {
      removedCount += part.value.split(/\s+/).filter(Boolean).length
    }
  })

  return (
    <div className="space-y-3">
      {/* Change summary */}
      <div className="flex items-center gap-4 text-xs">
        {addedCount > 0 && (
          <span className="text-green-600">+{addedCount} 词</span>
        )}
        {removedCount > 0 && (
          <span className="text-red-500">-{removedCount} 词</span>
        )}
      </div>

      {/* Diff content */}
      <div className="whitespace-pre-wrap text-sm leading-7 text-[var(--color-ink)]">
        {parts.map((part, index) => {
          if (part.added) {
            return (
              <span
                key={index}
                className="rounded-sm bg-[var(--color-diff-add-bg)] px-0.5 text-[var(--color-diff-add-text)]"
              >
                {part.value}
              </span>
            )
          }
          if (part.removed) {
            return (
              <span
                key={index}
                className="rounded-sm bg-[var(--color-diff-remove-bg)] px-0.5 text-[var(--color-diff-remove-text)] line-through"
              >
                {part.value}
              </span>
            )
          }
          return <span key={index}>{part.value}</span>
        })}
      </div>
    </div>
  )
}
