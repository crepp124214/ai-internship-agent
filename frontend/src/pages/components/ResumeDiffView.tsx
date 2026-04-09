// frontend/src/pages/components/ResumeDiffView.tsx
import { DiffContent } from './DiffContent'

interface ResumeDiffViewProps {
  title?: string
  original: string
  modified: string
  onAccept?: () => void
  onReject?: () => void
  loading?: boolean
}

export function ResumeDiffView({
  title = 'AI 修改建议',
  original,
  modified,
  onAccept,
  onReject,
  loading = false,
}: ResumeDiffViewProps) {
  return (
    <div className="space-y-4">
      {/* Header with title and actions */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[var(--color-ink)]">{title}</h3>
          <p className="text-xs text-[var(--color-muted)]">对比原简历内容</p>
        </div>
        <div className="flex items-center gap-2">
          {loading ? (
            <span className="text-xs text-[var(--color-muted)]">处理中...</span>
          ) : (
            <>
              <button
                type="button"
                onClick={onReject}
                className="inline-flex items-center gap-1.5 rounded-[8px] border border-transparent px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-secondary)] transition hover:bg-[var(--color-surface)]"
              >
                <span>拒绝</span>
              </button>
              <button
                type="button"
                onClick={onAccept}
                className="inline-flex items-center gap-1.5 rounded-[8px] bg-[var(--color-accent)] px-3 py-1.5 text-xs font-semibold text-white transition hover:opacity-90"
              >
                <span>接受</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Diff content */}
      <div className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-surface)] p-4">
        <DiffContent original={original} modified={modified} />
      </div>
    </div>
  )
}
