// frontend/src/pages/components/ScoreCard.tsx
interface ScoreCardProps {
  score: number
  label?: string
  comment?: string
}

export function ScoreCard({ score, label = '本题得分', comment }: ScoreCardProps) {
  // 分数颜色：80+ 绿，60-80 黄，60以下 红
  const getScoreColor = (s: number) => {
    if (s >= 80) return {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-600',
      badge: 'bg-emerald-100 text-emerald-700',
    }
    if (s >= 60) return {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-600',
      badge: 'bg-amber-100 text-amber-700',
    }
    return {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-600',
      badge: 'bg-red-100 text-red-700',
    }
  }

  const colors = getScoreColor(score)

  return (
    <div className={`inline-flex items-start gap-4 rounded-xl border p-4 ${colors.bg} ${colors.border}`}>
      {/* 大字体分数 */}
      <div className="flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold tracking-tight ${colors.text}`}>
          {score}
        </span>
        <span className={`text-xs font-medium uppercase tracking-wider mt-1 ${colors.badge}`}>
          分
        </span>
      </div>

      {/* 标签和评价 */}
      <div className="flex flex-col gap-1">
        <span className={`text-sm font-semibold ${colors.badge} px-2 py-0.5 rounded-md`}>
          {label}
        </span>
        {comment && (
          <p className="text-sm text-[var(--color-ink)] leading-relaxed max-w-[500px]">
            {comment}
          </p>
        )}
      </div>
    </div>
  )
}
