// frontend/src/pages/components/MessageBlock.tsx
import React from 'react'

interface MessageBlockProps {
  role: 'ai' | 'user'
  message: string
  timestamp?: string
}

const AIIcon = () => (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="8" fill="url(#ai-gradient)" />
    <path
      d="M18 8C12.477 8 8 12.477 8 18s4.477 10 10 10 10-4.477 10-10S23.523 8 18 8z"
      fill="white"
      fillOpacity="0.9"
    />
    <path
      d="M18 12v6l4 2"
      stroke="url(#ai-gradient)"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <defs>
      <linearGradient id="ai-gradient" x1="8" y1="8" x2="28" y2="28" gradientUnits="userSpaceOnUse">
        <stop stopColor="#6366F1" />
        <stop offset="1" stopColor="#8B5CF6" />
      </linearGradient>
    </defs>
  </svg>
)

const UserIcon = () => (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="8" fill="url(#user-gradient)" />
    <circle cx="18" cy="14" r="5" fill="white" fillOpacity="0.9" />
    <path
      d="M8 28c0-5.523 4.477-10 10-10s10 4.477 10 10"
      fill="white"
      fillOpacity="0.7"
    />
    <defs>
      <linearGradient id="user-gradient" x1="8" y1="8" x2="28" y2="28" gradientUnits="userSpaceOnUse">
        <stop stopColor="#10B981" />
        <stop offset="1" stopColor="#059669" />
      </linearGradient>
    </defs>
  </svg>
)

export function MessageBlock({ role, message, timestamp }: MessageBlockProps) {
  const isAI = role === 'ai'

  return (
    <div className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
      <div className={`flex items-end gap-3 max-w-[720px] ${isAI ? '' : 'flex-row-reverse'}`}>
        {/* Avatar - 36x36, 圆角 8px, 底部对齐 */}
        <div className="flex-shrink-0 rounded-[8px] overflow-hidden self-end">
          {isAI ? <AIIcon /> : <UserIcon />}
        </div>

        {/* 消息内容块 */}
        <div
          className={`px-4 py-3 ${
            isAI
              ? 'bg-transparent'
              : ''
          }`}
        >
          <div className="mb-1 flex items-center gap-2">
            <span className={`text-xs font-medium tracking-wide ${
              isAI ? 'text-[var(--color-accent)]' : 'text-[var(--color-muted)]'
            }`}>
              {isAI ? 'AI 面试官' : '你'}
            </span>
            {timestamp && (
              <span className="text-xs text-[var(--color-muted)]">{timestamp}</span>
            )}
          </div>
          <p
            className="text-[15px] leading-[1.7] text-[var(--color-ink)] whitespace-pre-wrap"
            style={{ wordBreak: 'break-word' }}
          >
            {message}
          </p>
        </div>
      </div>
    </div>
  )
}
