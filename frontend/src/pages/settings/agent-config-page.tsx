import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { getUserLlmConfigs, saveUserLlmConfig, deleteUserLlmConfig, type UserLlmConfig, type UserLlmConfigInput } from '../../lib/api'
import { readApiError } from '../../lib/api'
import { PageHeader } from '../page-primitives'
import { AgentConfigCard } from '../components/AgentConfigCard'

const AGENTS = [
  { id: 'resume_agent', label: '简历 Agent', description: '用于 JD 定制简历功能' },
  { id: 'job_agent', label: '岗位 Agent', description: '用于岗位推荐和搜索功能' },
  { id: 'interview_agent', label: '面试 Agent', description: '用于 AI 面试教练功能' },
]

interface ConfigFormData {
  agent: string
  provider: string
  model: string
  api_key: string
  base_url: string
  temperature: number
}

export function AgentConfigPage() {
  const queryClient = useQueryClient()
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const configsQuery = useQuery({
    queryKey: ['user-llm-configs'],
    queryFn: getUserLlmConfigs,
  })

  const configs: Record<string, UserLlmConfig> = {}
  configsQuery.data?.forEach((c) => {
    configs[c.agent] = c
  })

  const saveMutation = useMutation({
    mutationFn: (data: UserLlmConfigInput) => saveUserLlmConfig(data),
    onSuccess: (savedConfig) => {
      queryClient.setQueryData<UserLlmConfig[]>(['user-llm-configs'], (current = []) => {
        const filtered = current.filter((c) => c.agent !== savedConfig.agent)
        return [...filtered, savedConfig]
      })
      setExpandedAgent(null)
      setMessage({ type: 'success', text: '配置已保存' })
    },
    onError: (error) => {
      setMessage({ type: 'error', text: readApiError(error) })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (agent: string) => deleteUserLlmConfig(agent),
    onSuccess: (_, agent) => {
      queryClient.setQueryData<UserLlmConfig[]>(['user-llm-configs'], (current = []) => {
        return current.filter((c) => c.agent !== agent)
      })
      setExpandedAgent(null)
      setMessage({ type: 'success', text: '配置已删除' })
    },
    onError: (error) => {
      setMessage({ type: 'error', text: readApiError(error) })
    },
  })

  function handleToggle(agentId: string) {
    setMessage(null)
    setExpandedAgent((prev) => (prev === agentId ? null : agentId))
  }

  function handleSave(data: ConfigFormData) {
    const input: UserLlmConfigInput = {
      agent: data.agent,
      provider: data.provider,
      model: data.model,
      api_key: data.api_key,
      base_url: data.base_url || null,
      temperature: data.temperature,
    }
    saveMutation.mutate(input)
  }

  function handleDelete(agentId: string) {
    deleteMutation.mutate(agentId)
  }

  const activeMessage = expandedAgent ? message : null

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="系统设置"
        title="Agent 配置"
        description="为各个 Agent 自定义 LLM 配置，包括 Provider、模型和 API Key。"
      />

      {configsQuery.isError && (
        <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
          加载配置失败：{readApiError(configsQuery.error)}
        </div>
      )}

      {/* Global message for collapsed cards */}
      {!expandedAgent && message && (
        <div
          className={`rounded-2xl px-4 py-3 text-sm ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {AGENTS.map((agent) => (
          <AgentConfigCard
            key={agent.id}
            agentId={agent.id}
            config={configs[agent.id]}
            isExpanded={expandedAgent === agent.id}
            onToggle={() => handleToggle(agent.id)}
            onSave={handleSave}
            onDelete={() => handleDelete(agent.id)}
            saving={saveMutation.isPending || deleteMutation.isPending}
            message={activeMessage}
          />
        ))}
      </div>
    </div>
  )
}
