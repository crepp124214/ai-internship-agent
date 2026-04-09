import { useState, useCallback, useRef } from 'react'
import { getStoredToken } from '../auth/auth-storage'

export interface AssistantMessage {
  role: 'user' | 'ai' | 'system'
  content: string
}

export interface AssistantContext {
  page: 'resume' | 'job'
  resourceId?: number
  resourceIds?: number[]
}

export function useAgentAssistant() {
  const [messages, setMessages] = useState<AssistantMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (
    message: string,
    context: AssistantContext,
  ) => {
    // 取消之前的请求
    if (abortRef.current) {
      abortRef.current.abort()
    }
    abortRef.current = new AbortController()

    setStreaming(true)
    setError(null)

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: message }])

    let fullContent = ''

    try {
      const token = getStoredToken()
      const response = await fetch('/api/v1/agent/assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message,
          context: {
            page: context.page,
            resource_id: context.resourceId,
            resource_ids: context.resourceIds || [],
            history: messages.slice(-10).map(m => ({
              role: m.role === 'ai' ? 'assistant' : m.role,
              content: m.content,
            })),
          },
        }),
        signal: abortRef.current.signal,
      })

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'step') {
              fullContent += event.content
              setMessages(prev => {
                const last = prev[prev.length - 1]
                if (last?.role === 'ai') {
                  return [...prev.slice(0, -1), { role: 'ai', content: fullContent }]
                }
                return [...prev, { role: 'ai', content: fullContent }]
              })
            } else if (event.type === 'error') {
              setError(event.content)
            }
          } catch {}
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError((err as Error).message)
      }
    } finally {
      setStreaming(false)
    }
  }, [messages])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return {
    messages,
    streaming,
    error,
    sendMessage,
    clearMessages,
  }
}