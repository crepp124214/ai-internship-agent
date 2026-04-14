import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import {
  getUserLlmConfigs,
  saveUserLlmConfig,
  deleteUserLlmConfig,
  testGlobalLlmConfig,
  testAgentLlmConfig,
  type UserLlmConfig,
  type UserLlmConfigInput,
  type TestLlmConfigResponse,
} from '../../lib/api'
import { readApiError } from '../../lib/api'
import {
  FormField,
  Input,
  PageHeader,
  PrimaryButton,
  SectionCard,
  SecondaryButton,
  Select,
  StatusPill,
} from '../page-primitives'

const AGENTS = [
  { id: 'resume_agent', label: '简历 Agent', description: '用于 JD 定制简历功能' },
  { id: 'job_agent', label: '岗位 Agent', description: '用于岗位推荐和搜索功能' },
  { id: 'interview_agent', label: '面试 Agent', description: '用于 AI 面试教练功能' },
]

const AGENT_STATUS_LABELS: Record<string, { available: string; degraded: string; error: string; inactive: string }> = {
  resume_agent: { available: '简历 Agent 可用', degraded: '简历 Agent 降级中', error: '简历 Agent 异常', inactive: '简历 Agent 未配置' },
  job_agent: { available: '岗位 Agent 可用', degraded: '岗位 Agent 降级中', error: '岗位 Agent 异常', inactive: '岗位 Agent 未配置' },
  interview_agent: { available: '面试 Agent 可用', degraded: '面试 Agent 降级中', error: '面试 Agent 异常', inactive: '面试 Agent 未配置' },
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'zhipu', label: '智谱 AI' },
  { value: 'qwen', label: '通义千问' },
  { value: 'moonshot', label: 'Moonshot' },
  { value: 'siliconflow', label: 'SiliconFlow' },
]

const PROVIDER_CAPABILITIES: Record<string, { transport: string; note: string }> = {
  openai: {
    transport: 'Responses API 优先',
    note: '优先走 responses，适合原生 OpenAI 能力。',
  },
  minimax: {
    transport: 'Chat Completions',
    note: '跳过 responses，直接走 chat completion 兼容接口。',
  },
  zhipu: {
    transport: 'Chat Completions + 关闭 thinking',
    note: '为避免空正文响应，默认关闭 thinking 后再生成内容。',
  },
}

function getProviderCapability(provider?: string | null) {
  const key = provider?.toLowerCase() ?? ''
  return (
    PROVIDER_CAPABILITIES[key] ?? {
      transport: '标准兼容模式',
      note: '使用默认 OpenAI-compatible 调用路径。',
    }
  )
}

interface ConfigFormData {
  agent: string
  provider: string
  model: string
  api_key: string
  base_url: string
  temperature: number
}

function AgentStatusCard({
  agentId,
  config,
  testResult,
  onTest,
  testing,
  loading = false,
}: {
  agentId: string
  config: UserLlmConfig | undefined
  testResult: TestLlmConfigResponse | null
  onTest: () => void
  testing: boolean
  loading?: boolean
}) {
  const labels = AGENT_STATUS_LABELS[agentId] || { available: '可用', degraded: '降级中', error: '异常', inactive: '未配置' }

  if (loading) {
    const agent = AGENTS.find((a) => a.id === agentId)

    return (
      <div className="rounded-2xl border border-[var(--color-stroke)] bg-white p-5 shadow-[0_12px_40px_rgba(30,43,40,0.06)]">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-base font-semibold text-[var(--color-ink)]">{agent?.label}</h3>
            <p className="mt-1 text-xs text-[var(--color-muted)]">{agent?.description}</p>
          </div>
          <StatusPill>同步中</StatusPill>
        </div>

        <p className="mb-4 text-sm text-[var(--color-muted)]">正在同步 Agent 配置，请稍候...</p>

        <SecondaryButton type="button" onClick={onTest} disabled className="w-full">
          测试连接
        </SecondaryButton>
      </div>
    )
  }

  // Determine status based on test result or config presence
  let status: 'available' | 'degraded' | 'error' | 'inactive' = 'inactive'
  if (config) {
    if (testResult) {
      if (testResult.status === 'success') {
        status = 'available'
      } else if (testResult.fallback_used) {
        status = 'degraded'
      } else {
        status = 'error'
      }
    } else {
      // Config exists but not tested yet - show as available (inherited)
      status = 'available'
    }
  }

  const statusLabel = labels[status]
  const statusClassName =
    status === 'available'
      ? 'bg-green-50 text-green-700 border-green-200'
      : status === 'degraded'
        ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
        : status === 'error'
          ? 'bg-red-50 text-red-700 border-red-200'
          : 'bg-gray-50 text-gray-500 border-gray-200'

  const agent = AGENTS.find((a) => a.id === agentId)
  const capability = getProviderCapability(config?.provider)

  return (
    <div className="rounded-2xl border border-[var(--color-stroke)] bg-white p-5 shadow-[0_12px_40px_rgba(30,43,40,0.06)]">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-base font-semibold text-[var(--color-ink)]">{agent?.label}</h3>
          <p className="mt-1 text-xs text-[var(--color-muted)]">{agent?.description}</p>
        </div>
        <StatusPill>{statusLabel}</StatusPill>
      </div>

      {config ? (
        <div className="mb-4 space-y-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Provider</p>
              <p className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">{config.provider}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Model</p>
              <p className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">{config.model}</p>
            </div>
          </div>
          <div className="rounded-xl bg-[var(--color-surface)] px-3 py-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">兼容策略</p>
            <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">{capability.transport}</p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">{capability.note}</p>
          </div>
          {testResult && (
            <div className={`mt-3 rounded-xl border px-3 py-2 text-xs ${statusClassName}`}>
              {testResult.status === 'success' ? (
                <span>响应 {testResult.latency_ms}ms{testResult.fallback_used ? ' · 降级模式' : ''}</span>
              ) : (
                <span className="font-medium">{testResult.error_code}: </span>
              )}
              {testResult.error_message && <span>{testResult.error_message}</span>}
            </div>
          )}
        </div>
      ) : (
        <p className="mb-4 text-sm text-[var(--color-muted)]">暂无独立配置，使用批量配置</p>
      )}

      <SecondaryButton type="button" onClick={onTest} disabled={testing} className="w-full">
        {testing ? '测试中...' : '测试连接'}
      </SecondaryButton>
    </div>
  )
}

export function AgentConfigPage() {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, TestLlmConfigResponse | null>>({})
  const [testingAgents, setTestingAgents] = useState<Record<string, boolean>>({})

  // Global config form state
  const [globalProvider, setGlobalProvider] = useState('openai')
  const [globalModel, setGlobalModel] = useState('')
  const [globalApiKey, setGlobalApiKey] = useState('')
  const [globalBaseUrl, setGlobalBaseUrl] = useState('')
  const [globalTemperature, setGlobalTemperature] = useState(0.7)

  const configsQuery = useQuery({
    queryKey: ['user-llm-configs'],
    queryFn: getUserLlmConfigs,
  })

  const configsList = configsQuery.data ?? []
  const isConfigSyncing = configsQuery.isLoading && configsList.length === 0

  const configs: Record<string, UserLlmConfig> = {}
  configsList.forEach((c) => {
    configs[c.agent] = c
  })
  const sharedProvider = isConfigSyncing
    ? null
    : configs['resume_agent']?.provider ?? configs['job_agent']?.provider ?? configs['interview_agent']?.provider ?? null
  const sharedCapability = getProviderCapability(sharedProvider)

  // Batch config form state (shared across all agents when using batch edit)
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

  const testGlobalMutation = useMutation({
    mutationFn: (data: { provider: string; model: string; api_key: string; base_url?: string | null }) =>
      testGlobalLlmConfig(data),
    onSuccess: (result) => {
      // Update all agents with the same test result
      const newResults: Record<string, TestLlmConfigResponse | null> = {}
      AGENTS.forEach((agent) => {
        newResults[agent.id] = { ...result, agent: agent.id }
      })
      setTestResults(newResults)
    },
    onError: (error) => {
      setMessage({ type: 'error', text: `测试失败: ${readApiError(error)}` })
    },
  })

  const testAgentMutation = useMutation({
    mutationFn: ({ agent, data }: { agent: string; data: { provider: string; model: string; api_key: string; base_url?: string | null } }) =>
      testAgentLlmConfig(agent, data),
    onSuccess: (result, variables) => {
      setTestResults((prev) => ({ ...prev, [variables.agent]: result }))
    },
    onError: (error, variables) => {
      const errorResult: TestLlmConfigResponse = {
        status: 'error',
        error_code: 'TEST_FAILED',
        error_message: readApiError(error),
        latency_ms: 0,
        fallback_used: false,
        provider: '',
        model: '',
        agent: variables.agent,
      }
      setTestResults((prev) => ({ ...prev, [variables.agent]: errorResult }))
    },
  })

  function handleEdit(agentId: string) {
    setMessage(null)
    setEditing(agentId)
    // Populate form with existing config or global defaults
    const config = configs[agentId]
    if (config) {
      setGlobalProvider(config.provider.toLowerCase())
      setGlobalModel(config.model)
      setGlobalApiKey(config.api_key ?? '')
      setGlobalBaseUrl(config.base_url ?? '')
      setGlobalTemperature(config.temperature)
    } else {
      setGlobalProvider('openai')
      setGlobalModel('')
      setGlobalApiKey('')
      setGlobalBaseUrl('')
      setGlobalTemperature(0.7)
    }
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
    // When editing global config, save for all three agents
    if (editing === 'global') {
      AGENTS.forEach((agent) => {
        saveMutation.mutate({ ...input, agent: agent.id })
      })
    } else {
      saveMutation.mutate(input)
    }
  }

  function handleDelete(agentId: string) {
    deleteMutation.mutate(agentId)
  }

  function handleTestGlobal() {
    if (!globalApiKey.trim() || !globalModel.trim()) {
      setMessage({ type: 'error', text: '请填写 API Key 和模型名称' })
      return
    }
    testGlobalMutation.mutate({
      provider: globalProvider,
      model: globalModel,
      api_key: globalApiKey,
      base_url: globalBaseUrl || null,
    })
  }

  function handleTestAgent(agentId: string) {
    const config = configs[agentId]
    if (!config) {
      setMessage({ type: 'error', text: '该 Agent 未配置独立设置' })
      return
    }
    setTestingAgents((prev) => ({ ...prev, [agentId]: true }))
    testAgentMutation.mutate(
      { agent: agentId, data: {
        provider: config.provider.toLowerCase(),
        model: config.model,
        api_key: config.api_key ?? '',
        base_url: config.base_url,
      }},
      {
        onSettled: () => {
          setTestingAgents((prev) => ({ ...prev, [agentId]: false }))
        },
      }
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="系统设置"
        title="Agent 配置"
        description="批量配置三个 Agent 的 LLM 设置、查看状态、测试连接和高级覆盖。"
      />

      {configsQuery.isError && (
        <div className="rounded-[22px] bg-red-50 px-4 py-3 text-sm text-red-700">
          加载配置失败：{readApiError(configsQuery.error)}
        </div>
      )}

      {/* Batch Config Section */}
      <SectionCard
        title="批量配置 Agent"
        subtitle="一次配置同时应用到简历、岗位、面试三个 Agent（保存为三份独立配置）"
      >
        {editing === 'global' ? (
          <form onSubmit={(e) => {
            e.preventDefault()
            if (!globalModel.trim() || !globalApiKey.trim()) return
            handleSave({
              agent: 'resume_agent',
              provider: globalProvider,
              model: globalModel,
              api_key: globalApiKey,
              base_url: globalBaseUrl,
              temperature: globalTemperature,
            })
          }} className="space-y-4">
            <FormField label="Provider">
              <Select value={globalProvider} onChange={(e) => setGlobalProvider(e.target.value)}>
                {PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </Select>
            </FormField>
            <FormField label="Model">
              <Input
                value={globalModel}
                onChange={(e) => setGlobalModel(e.target.value)}
                placeholder="例如：gpt-4o-mini"
              />
            </FormField>
            <FormField label="API Key">
              <Input
                type="password"
                value={globalApiKey}
                onChange={(e) => setGlobalApiKey(e.target.value)}
                placeholder="sk-..."
              />
            </FormField>
            <FormField label="Base URL（可选）">
              <Input
                value={globalBaseUrl}
                onChange={(e) => setGlobalBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
              />
            </FormField>
            <FormField label={`Temperature: ${globalTemperature}`}>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={globalTemperature}
                onChange={(e) => setGlobalTemperature(parseFloat(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-[var(--color-ink-muted)]">控制输出的随机性，值越低越确定性</span>
            </FormField>

            {message && (
              <div className={`rounded-[22px] px-4 py-3 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {message.text}
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              <PrimaryButton type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? '保存中...' : '批量保存到三个 Agent'}
              </PrimaryButton>
              <SecondaryButton type="button" onClick={() => { setEditing(null); setMessage(null) }}>
                取消
              </SecondaryButton>
              <SecondaryButton type="button" onClick={handleTestGlobal} disabled={testGlobalMutation.isPending}>
                {testGlobalMutation.isPending ? '测试中...' : '测试连接'}
              </SecondaryButton>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Provider</p>
                <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">
                  {isConfigSyncing ? '同步中...' : configs['resume_agent']?.provider ?? configs['job_agent']?.provider ?? configs['interview_agent']?.provider ?? '未设置'}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Model</p>
                <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">
                  {isConfigSyncing ? '同步中...' : configs['resume_agent']?.model ?? configs['job_agent']?.model ?? configs['interview_agent']?.model ?? '未设置'}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Temperature</p>
                <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">
                  {isConfigSyncing ? '同步中...' : configs['resume_agent']?.temperature ?? configs['job_agent']?.temperature ?? 0.7}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">已配置</p>
                <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">
                  {isConfigSyncing ? '同步配置中...' : `${configsList.length} / 3 个 Agent`}
                </p>
              </div>
            </div>
            <div className="rounded-xl bg-[var(--color-surface)] px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">当前兼容策略</p>
              <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">{sharedCapability.transport}</p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">{sharedCapability.note}</p>
            </div>
            {testGlobalMutation.data && (
              <div className={`rounded-xl border px-4 py-3 text-sm ${testGlobalMutation.data.status === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}`}>
                {testGlobalMutation.data.status === 'success' ? (
                  <span>连接成功 · 响应 {testGlobalMutation.data.latency_ms}ms{testGlobalMutation.data.fallback_used ? ' · 降级模式' : ''}</span>
                ) : (
                  <>
                    <span className="font-medium">{testGlobalMutation.data.error_code}: </span>
                    <span>{testGlobalMutation.data.error_message}</span>
                  </>
                )}
              </div>
            )}
            <SecondaryButton type="button" onClick={() => handleEdit('global')}>
              批量配置
            </SecondaryButton>
          </div>
        )}
      </SectionCard>

      {/* Agent Status Grid */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-ink)]">Agent 状态</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {AGENTS.map((agent) => (
            <AgentStatusCard
              key={agent.id}
              agentId={agent.id}
              config={configs[agent.id]}
              testResult={testResults[agent.id] ?? null}
              onTest={() => handleTestAgent(agent.id)}
              testing={testingAgents[agent.id] ?? false}
              loading={isConfigSyncing}
            />
          ))}
        </div>
      </div>

      {/* Connection Test Panel */}
      <SectionCard title="连接测试" subtitle="测试 LLM 配置的 API 连通性（使用批量配置的凭证）">
        <div className="space-y-4">
          <p className="text-sm text-[var(--color-muted)]">
            上方的 Agent 状态卡片已包含快速测试按钮。也可在此处进行详细测试：
          </p>
          <div className="flex flex-wrap gap-3">
            <SecondaryButton
              type="button"
              onClick={handleTestGlobal}
              disabled={testGlobalMutation.isPending || !globalApiKey.trim()}
            >
              {testGlobalMutation.isPending ? '测试中...' : '测试连接'}
            </SecondaryButton>
          </div>
          {testGlobalMutation.data && (
            <div className={`rounded-xl border px-4 py-3 text-sm ${testGlobalMutation.data.status === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}`}>
              {testGlobalMutation.data.status === 'success' ? (
                <div>
                  <p>状态：成功</p>
                  <p>Provider：{testGlobalMutation.data.provider}</p>
                  <p>Model：{testGlobalMutation.data.model}</p>
                  <p>延迟：{testGlobalMutation.data.latency_ms}ms</p>
                  {testGlobalMutation.data.fallback_used && <p className="mt-1 text-yellow-600">⚠️ 降级模式已启用</p>}
                </div>
              ) : (
                <div>
                  <p className="font-medium">错误码：{testGlobalMutation.data.error_code}</p>
                  <p>{testGlobalMutation.data.error_message}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </SectionCard>

      {/* Advanced Override Disclosure */}
      <SectionCard
        title="高级覆盖配置"
        subtitle={editing && editing !== 'global' ? `正在编辑: ${AGENTS.find(a => a.id === editing)?.label}` : '为单个 Agent 单独配置，与批量配置相互独立'}
      >
        {!showAdvanced ? (
          <SecondaryButton type="button" onClick={() => setShowAdvanced(true)}>
            展开高级配置
          </SecondaryButton>
        ) : (
          <div className="space-y-4">
            {editing && editing !== 'global' ? (
              <form onSubmit={(e) => {
                e.preventDefault()
                if (!globalModel.trim() || !globalApiKey.trim()) return
                handleSave({
                  agent: editing,
                  provider: globalProvider,
                  model: globalModel,
                  api_key: globalApiKey,
                  base_url: globalBaseUrl,
                  temperature: globalTemperature,
                })
              }} className="space-y-4">
                <p className="text-sm font-medium text-[var(--color-ink)]">
                  为 {AGENTS.find(a => a.id === editing)?.label} 单独配置：
                </p>
                <FormField label="Provider">
                  <Select value={globalProvider} onChange={(e) => setGlobalProvider(e.target.value)}>
                    {PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </Select>
                </FormField>
                <FormField label="Model">
                  <Input
                    value={globalModel}
                    onChange={(e) => setGlobalModel(e.target.value)}
                    placeholder="例如：gpt-4o-mini"
                  />
                </FormField>
                <FormField label="API Key">
                  <Input
                    type="password"
                    value={globalApiKey}
                    onChange={(e) => setGlobalApiKey(e.target.value)}
                    placeholder="sk-..."
                  />
                </FormField>
                <FormField label="Base URL（可选）">
                  <Input
                    value={globalBaseUrl}
                    onChange={(e) => setGlobalBaseUrl(e.target.value)}
                    placeholder="https://api.openai.com/v1"
                  />
                </FormField>
                <FormField label={`Temperature: ${globalTemperature}`}>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={globalTemperature}
                    onChange={(e) => setGlobalTemperature(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </FormField>

                {message && (
                  <div className={`rounded-[22px] px-4 py-3 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {message.text}
                  </div>
                )}

                <div className="flex flex-wrap gap-3">
                  <PrimaryButton type="submit" disabled={saveMutation.isPending}>
                    {saveMutation.isPending ? '保存中...' : '保存'}
                  </PrimaryButton>
                  <SecondaryButton type="button" onClick={() => { setEditing(null); setMessage(null) }}>
                    取消
                  </SecondaryButton>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                {AGENTS.map((agent) => (
                  <div key={agent.id} className="flex items-center justify-between rounded-xl border border-[var(--color-stroke)] p-4">
                    <div>
                      <p className="font-medium text-[var(--color-ink)]">{agent.label}</p>
                      <p className="text-xs text-[var(--color-muted)]">
                        {configs[agent.id] ? `${configs[agent.id].provider} · ${configs[agent.id].model}` : '无独立配置'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {configs[agent.id] && (
                        <SecondaryButton type="button" onClick={() => handleDelete(agent.id)}>
                          删除
                        </SecondaryButton>
                      )}
                      <SecondaryButton type="button" onClick={() => handleEdit(agent.id)}>
                        {configs[agent.id] ? '修改' : '覆盖'}
                      </SecondaryButton>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <SecondaryButton type="button" onClick={() => { setShowAdvanced(false); setEditing(null) }}>
              收起高级配置
            </SecondaryButton>
          </div>
        )}
      </SectionCard>
    </div>
  )
}
