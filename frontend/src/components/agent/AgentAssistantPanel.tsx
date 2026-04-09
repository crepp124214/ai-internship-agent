// frontend/src/components/agent/AgentAssistantPanel.tsx
import { useEffect, useRef, useState } from 'react'
import { useAgentAssistant, type AssistantMessage } from '../../hooks/useAgentAssistant'
import { SecondaryButton } from '../../pages/page-primitives'

interface QuickAction {
  label: string
  message: string
}

interface AgentAssistantPanelProps {
  page: 'resume' | 'job'
  resourceId?: number
  resourceIds?: number[]
  quickActions?: QuickAction[]
}

export function AgentAssistantPanel({
  page,
  resourceId,
  resourceIds,
  quickActions = [],
}: AgentAssistantPanelProps) {
  const { messages, streaming, error, sendMessage, clearMessages } = useAgentAssistant()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 页面切换时清空消息
  useEffect(() => {
    clearMessages()
  }, [page, clearMessages])

  function handleSend(message: string) {
    if (!message.trim() || streaming) return
    sendMessage(message, { page, resourceId, resourceIds })
    setInput('')
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    handleSend(input)
  }

  function handleQuickAction(action: QuickAction) {
    handleSend(action.message)
  }

  return (
    <div className="flex flex-col h-full border-l border-[var(--color-border)] bg-[var(--color-surface)]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <h3 className="text-sm font-semibold text-[var(--color-ink)]">Agent 助手</h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && !streaming && (
          <div className="text-sm text-[var(--color-ink-muted)]">
            {page === 'resume'
              ? '选中一份简历，我可以帮您分析、解读或给出改进建议。'
              : '我可以帮您搜索公司招聘官网，或分析岗位与简历的匹配度。'}
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {streaming && (
          <div className="text-sm text-[var(--color-ink-muted)]">
            <span className="animate-pulse">思考中...</span>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600 bg-red-50 rounded-[22px] px-4 py-3">
            错误：{error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {quickActions.length > 0 && messages.length === 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {quickActions.map((action, i) => (
            <SecondaryButton
              key={i}
              onClick={() => handleQuickAction(action)}
              disabled={streaming}
            >
              {action.label}
            </SecondaryButton>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-[var(--color-border)]">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend(input)
              }
            }}
            placeholder={page === 'resume' ? '问关于简历的问题...' : '搜索岗位或分析简历...'}
            className="flex-1 resize-none rounded-[22px] border border-[var(--color-border)] px-4 py-2 text-sm focus:outline-none focus:border-[var(--color-primary)]"
            rows={1}
            disabled={streaming}
          />
          <SecondaryButton type="submit" disabled={streaming || !input.trim()}>
            发送
          </SecondaryButton>
        </div>
      </form>
    </div>
  )
}

function MessageBubble({ message }: { message: AssistantMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-[22px] px-4 py-3 text-sm ${
          isUser
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-[var(--color-background)] text-[var(--color-ink)] border border-[var(--color-border)]'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}
