interface ChatBubbleProps {
  role: 'ai' | 'user'
  message: string
  score?: number | null
  timestamp?: string
}

export function ChatBubble({ role, message, score, timestamp }: ChatBubbleProps) {
  const isAI = role === 'ai'

  return (
    <div className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[80%] rounded-3xl px-5 py-3 text-sm leading-7 ${
          isAI
            ? 'bg-[var(--color-surface)] text-[var(--color-ink)] rounded-bl-md'
            : 'bg-[var(--color-accent)] text-white rounded-br-md'
        }`}
      >
        <div className="mb-1 flex items-center gap-2">
          <span className={`text-xs font-semibold uppercase tracking-wider ${
            isAI ? 'text-[var(--color-accent)]' : 'text-white/70'
          }`}>
            {isAI ? 'AI 面试官' : '你'}
          </span>
          {score !== undefined && score !== null && isAI && (
            <span className="rounded-full bg-[var(--color-accent)] px-2 py-0.5 text-xs font-bold text-white">
              {score}分
            </span>
          )}
          {timestamp && (
            <span className="text-xs text-[var(--color-ink-muted)]">{timestamp}</span>
          )}
        </div>
        <p className="whitespace-pre-wrap">{message}</p>
      </div>
    </div>
  )
}
