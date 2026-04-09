// frontend/src/pages/components/JobCard.tsx
import { clsx } from 'clsx'
import type { Job } from '../../lib/api'
import { MatchBadge } from './MatchBadge'

interface JobCardProps {
  job: Job
  isSelected?: boolean
  matchScore?: number // 0-100, if available
  onClick?: () => void
  onDoubleClick?: () => void
}

function TagList({ tags }: { tags: string | null }) {
  if (!tags) return null
  const tagArray = tags.split(',').map((t) => t.trim()).filter(Boolean)
  if (tagArray.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1.5">
      {tagArray.slice(0, 5).map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center rounded-full bg-[var(--color-panel)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-muted)]"
        >
          {tag}
        </span>
      ))}
      {tagArray.length > 5 && (
        <span className="inline-flex items-center rounded-full bg-[var(--color-panel)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-muted)]">
          +{tagArray.length - 5}
        </span>
      )}
    </div>
  )
}

export function JobCard({ job, isSelected = false, matchScore, onClick, onDoubleClick }: JobCardProps) {
  return (
    <article
      role="button"
      tabIndex={0}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' && !e.metaKey && !e.ctrlKey) {
          e.preventDefault()
          onClick?.()
        }
        if ((e.key === 'Enter') && (e.metaKey || e.ctrlKey)) {
          e.preventDefault()
          onDoubleClick?.()
        }
      }}
      className={clsx(
        'group cursor-pointer rounded-[20px] border p-4 transition-all hover:scale-[1.01]',
        isSelected
          ? 'border-[var(--color-accent)] bg-[var(--color-surface)]'
          : 'border-[var(--color-border-subtle)] bg-[var(--color-surface)] hover:border-[var(--color-accent)]',
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-semibold text-[var(--color-ink)] group-hover:text-[var(--color-accent)]">
            {job.title}
          </h3>
          <p className="mt-0.5 truncate text-sm text-[var(--color-muted)]">{job.company}</p>
        </div>
        {matchScore !== undefined && (
          <MatchBadge score={matchScore} size="sm" />
        )}
      </div>

      <div className="mb-3 flex items-center gap-3 text-xs text-[var(--color-muted)]">
        {job.location && (
          <span className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {job.location}
          </span>
        )}
        {job.work_type && (
          <span className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            {job.work_type}
          </span>
        )}
        {job.salary && (
          <span className="flex items-center gap-1 font-medium text-[var(--color-ink-secondary)]">
            {job.salary}
          </span>
        )}
      </div>

      <TagList tags={job.tags} />

      {job.source_url && (
        <a
          href={job.source_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="mt-3 inline-flex items-center gap-1 text-xs text-[var(--color-muted)] hover:text-[var(--color-accent)]"
        >
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          查看来源
        </a>
      )}
    </article>
  )
}
