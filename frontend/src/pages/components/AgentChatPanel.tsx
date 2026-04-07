// frontend/src/pages/components/AgentChatPanel.tsx
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../../auth/use-auth'

interface Message {
  role: 'user' | 'ai'
  content: string
}

interface AgentChatPanelProps {
  initialTask?: string
}

export function AgentChatPanel({ initialTask }: AgentChatPanelProps) {
  const { token } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState(initialTask || '')
  const [streaming, setStreaming] = useState(false)
  const [currentAiContent, setCurrentAiContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentAiContent])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || streaming) return

    const userMessage = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setStreaming(true)
    setCurrentAiContent('')

    try {
      const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')
      const response = await fetch(`${apiBaseUrl}/api/v1/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ task: userMessage, context: {} }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Stream failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false
      let accumulated = ''

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value, { stream: !doneReading })
          const lines = chunk.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6))
                if (event.type === 'step' && event.step === 'final') {
                  accumulated += event.content
                  setCurrentAiContent(accumulated)
                } else if (event.type === 'done') {
                  // 流结束
                }
              } catch {
                // ignore parse errors
              }
            }
          }
        }
      }

      if (accumulated) {
        setMessages(prev => [...prev, { role: 'ai', content: accumulated }])
      }
      setCurrentAiContent('')
    } catch (err) {
      console.error('Stream error:', err)
      setMessages(prev => [...prev, { role: 'ai', content: '抱歉，发生了错误，请稍后重试。' }])
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-[var(--color-accent)] text-white rounded-br-md'
                  : 'bg-[var(--color-surface)] text-[var(--color-ink)] rounded-bl-md'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {/* 流式输出中 */}
        {streaming && currentAiContent && (
          <div className="flex justify-start">
            <div className="bg-[var(--color-surface)] text-[var(--color-ink)] rounded-2xl rounded-bl-md px-4 py-3 text-sm max-w-[80%]">
              <p className="whitespace-pre-wrap">{currentAiContent}<span className="animate-pulse">█</span></p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <form onSubmit={handleSubmit} className="border-t border-[var(--color-stroke)] p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="输入你的求职问题..."
            disabled={streaming}
            className="flex-1 rounded-full border border-[var(--color-stroke)] bg-white px-5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="rounded-full bg-[var(--color-accent)] px-6 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  )
}
