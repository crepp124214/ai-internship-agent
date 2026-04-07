// frontend/src/pages/components/MatchReportCard.tsx
import type { MatchReportData } from '../../lib/api'

interface MatchReportCardProps {
  report: MatchReportData
}

export function MatchReportCard({ report }: MatchReportCardProps) {
  const scorePercent = Math.round(report.match_score * 100)
  const coveredCount = Object.values(report.keyword_coverage).filter(Boolean).length
  const totalCount = Object.keys(report.keyword_coverage).length

  return (
    <div className="space-y-4">
      {/* Score */}
      <div className="flex items-center gap-3">
        <div className="text-3xl font-semibold text-[var(--color-accent)]">
          {scorePercent}%
        </div>
        <div className="text-sm text-[var(--color-muted)]">匹配度</div>
      </div>

      {/* Keyword coverage bar */}
      {totalCount > 0 && (
        <div>
          <div className="mb-1 flex justify-between text-xs text-[var(--color-muted)]">
            <span>关键词覆盖</span>
            <span>{coveredCount}/{totalCount}</span>
          </div>
          <div className="h-2 w-full rounded-full bg-[var(--color-panel)]">
            <div
              className="h-2 rounded-full bg-[var(--color-accent)] transition-all"
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Keyword list */}
      {Object.keys(report.keyword_coverage).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(report.keyword_coverage).map(([keyword, covered]) => (
            <span
              key={keyword}
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                covered
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {covered ? '✓' : '✗'} {keyword}
            </span>
          ))}
        </div>
      )}

      {/* Gaps */}
      {report.gaps.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
            差距项
          </p>
          <ul className="space-y-1">
            {report.gaps.map((gap) => (
              <li key={gap} className="flex items-start gap-2 text-sm text-[var(--color-ink)]">
                <span className="text-red-500">•</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {report.suggestions.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
            改进建议
          </p>
          <ul className="space-y-1">
            {report.suggestions.map((suggestion, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-ink)]">
                <span className="text-[var(--color-accent)]">→</span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
