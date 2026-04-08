import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { getUserLlmConfigs, saveUserLlmConfig, deleteUserLlmConfig, type UserLlmConfig, type UserLlmConfigInput } from '../../lib/api'
import { readApiError } from '../../lib/api'
import {
  FormField,
  Input,
  PageHeader,
  PrimaryButton,
  SectionCard,
  SecondaryButton,
  Select,
} from '../page-primitives'

const AGENTS = [
  { id: 'resume_agent', label: '简历 Agent', description: '用于 JD 定制简历功能' },
  { id: 'job_agent', label: '岗位 Agent', description: '用于岗位推荐和搜索功能' },
  { id: 'interview_agent', label: '面试 Agent', description: '用于 AI 面试教练功能' },
]

const PROVIDERS = [
  'OpenAI',
  'Anthropic',
  'MiniMax',
  'DeepSeek',
  '智谱 AI',
  '通义千问',
  'Moonshot',
  'SiliconFlow',
]

interface ConfigFormData {
  agent: string
  provider: string
  model: string
  api_key: string
  base_url: string
  temperature: number
}

function AgentCard({
  agent,
  config,
  isEditing,
  onEdit,
  onCancel,
  onSave,
  onDelete,
  saving,
  message,
}: {
  agent: typeof AGENTS[number]
  config: UserLlmConfig | undefined
  isEditing: boolean
  onEdit: () => void
  onCancel: () => void
  onSave: (data: ConfigFormData) => void
  onDelete: () => void
  saving: boolean
  message: { type: 'success' | 'error'; text: string } | null
}) {
  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<ConfigFormData>({
    defaultValues: {
      agent: agent.id,
      provider: config?.provider ?? 'OpenAI',
      model: config?.model ?? '',
      api_key: config?.api_key ?? '',
      base_url: config?.base_url ?? '',
      temperature: config?.temperature ?? 0.7,
    },
  })

  const watchedTemperature = watch('temperature')

  useEffect(() => {
    if (isEditing && config) {
      reset({
        agent: agent.id,
        provider: config.provider ?? 'OpenAI',
        model: config.model ?? '',
        api_key: config.api_key ?? '',
        base_url: config.base_url ?? '',
        temperature: config.temperature ?? 0.7,
      })
    } else if (isEditing) {
      reset({
        agent: agent.id,
        provider: 'OpenAI',
        model: '',
        api_key: '',
        base_url: '',
        temperature: 0.7,
      })
    }
  }, [isEditing, config, agent.id, reset])

  if (isEditing) {
    return (
      <SectionCard title={agent.label} subtitle={agent.description}>
        <form onSubmit={handleSubmit(onSave)} className="space-y-4">
          <FormField label="Provider">
            <Select {...register('provider', { required: '请选择 Provider' })}>
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </Select>
          </FormField>

          <FormField label="Model">
            <Input
              {...register('model', { required: '请输入模型名称' })}
              placeholder="例如：gpt-4o-mini"
            />
          </FormField>

          <FormField label="API Key">
            <Input
              type="password"
              {...register('api_key', { required: '请输入 API Key' })}
              placeholder="sk-..."
            />
          </FormField>

          <FormField label="Base URL（可选）">
            <Input
              {...register('base_url')}
              placeholder="https://api.openai.com/v1"
            />
          </FormField>

          <FormField label={`Temperature: ${watchedTemperature}`}>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              {...register('temperature', { valueAsNumber: true })}
              className="w-full"
            />
            <span className="text-xs text-[var(--color-muted)]">控制输出的随机性，值越低越确定性</span>
          </FormField>

          {message ? (
            <div className={`rounded-[22px] px-4 py-3 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {message.text}
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <PrimaryButton type="submit" disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </PrimaryButton>
            <SecondaryButton type="button" onClick={onCancel}>
              取消
            </SecondaryButton>
            {config && (
              <SecondaryButton type="button" onClick={onDelete}>
                删除配置
              </SecondaryButton>
            )}
          </div>
        </form>
      </SectionCard>
    )
  }

  return (
    <SectionCard title={agent.label} subtitle={agent.description}>
      <div className="space-y-4">
        {config ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Provider</p>
                <p className="mt-1 text-sm text-[var(--color-ink)]">{config.provider}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Model</p>
                <p className="mt-1 text-sm text-[var(--color-ink)]">{config.model}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Temperature</p>
                <p className="mt-1 text-sm text-[var(--color-ink)]">{config.temperature}</p>
              </div>
              {config.base_url && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Base URL</p>
                  <p className="mt-1 text-sm text-[var(--color-ink)]">{config.base_url}</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-[var(--color-muted)]">使用系统默认配置</p>
        )}

        {message ? (
          <div className={`rounded-[22px] px-4 py-3 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.text}
          </div>
        ) : null}

        <SecondaryButton type="button" onClick={onEdit}>
          {config ? '编辑配置' : '自定义配置'}
        </SecondaryButton>
      </div>
    </SectionCard>
  )
}

export function AgentConfigPage() {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<string | null>(null)
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
      setEditing(null)
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
      setEditing(null)
      setMessage({ type: 'success', text: '配置已删除' })
    },
    onError: (error) => {
      setMessage({ type: 'error', text: readApiError(error) })
    },
  })

  function handleEdit(agentId: string) {
    setMessage(null)
    setEditing(agentId)
  }

  function handleCancel() {
    setEditing(null)
    setMessage(null)
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

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="系统设置"
        title="Agent 配置"
        description="为各个 Agent 自定义 LLM 配置，包括 Provider、模型和 API Key。"
      />

      {configsQuery.isError && (
        <div className="rounded-[22px] bg-red-50 px-4 py-3 text-sm text-red-700">
          加载配置失败：{readApiError(configsQuery.error)}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {AGENTS.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            config={configs[agent.id]}
            isEditing={editing === agent.id}
            onEdit={() => handleEdit(agent.id)}
            onCancel={handleCancel}
            onSave={handleSave}
            onDelete={() => handleDelete(agent.id)}
            saving={saveMutation.isPending || deleteMutation.isPending}
            message={message}
          />
        ))}
      </div>
    </div>
  )
}
