// frontend/src/pages/components/CoachReviewReportCard.tsx
interface ReviewReportDimension {
  name: string
  score: number
  stars: number
  suggestion: string
}

interface ReviewReport {
  dimensions: ReviewReportDimension[]
  overall_score: number
  overall_comment: string
  improvement_suggestions: string[]
  markdown: string
}

interface CoachReviewReportCardProps {
  report: ReviewReport
  averageScore: number
}

export function CoachReviewReportCard({ report, averageScore }: CoachReviewReportCardProps) {
  const scorePercent = Math.round(averageScore)

  return (
    <div className="space-y-5">
      {/* Overall */}
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-[var(--color-accent)]">{scorePercent}</div>
        <div>
          <div className="text-sm text-[var(--color-muted)]">综合评分</div>
          <div className="text-lg">
            {'★'.repeat(Math.ceil(scorePercent / 20))}{'☆'.repeat(5 - Math.ceil(scorePercent / 20))}
          </div>
        </div>
      </div>

      {/* Dimensions */}
      <div className="grid gap-3 sm:grid-cols-2">
        {report.dimensions.map((dim: ReviewReportDimension) => (
          <div key={dim.name} className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-surface)] p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-[var(--color-ink)]">{dim.name}</span>
              <span className="text-sm font-bold text-[var(--color-accent)]">{dim.score}分</span>
            </div>
            <div className="mb-2 h-1.5 w-full rounded-full bg-[var(--color-panel)]">
              <div
                className="h-1.5 rounded-full bg-[var(--color-accent)] transition-all"
                style={{ width: `${dim.score}%` }}
              />
            </div>
            <p className="text-xs text-[var(--color-muted)]">{dim.suggestion}</p>
          </div>
        ))}
      </div>

      {/* Overall comment */}
      <div className="rounded-2xl border border-[var(--color-accent)] bg-[var(--color-accent)]/5 p-4">
        <p className="text-sm font-medium text-[var(--color-ink)]">{report.overall_comment}</p>
      </div>

      {/* Suggestions */}
      {report.improvement_suggestions.length > 0 && (
        <div>
          <p className="mb-3 text-sm font-semibold text-[var(--color-ink)]">改进建议</p>
          <ul className="space-y-2">
            {report.improvement_suggestions.map((sug: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-ink)]">
                <span className="text-[var(--color-accent)]">→</span>
                {sug}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}