import { useState } from 'react'
import { clsx } from 'clsx'
import { PROVIDERS } from './ProviderSelector'

const AGENT_META = {
  resume_agent: { icon: '📄', label: '简历 Agent' },
  job_agent: { icon: '💼', label: '岗位 Agent' },
  interview_agent: { icon: '🎯', label: '面试 Agent' },
} as const

interface ConfigFormData {
  agent: string
  provider: string
  model: string
  api_key: string
  base_url: string
  temperature: number
}

interface AgentConfigCardProps {
  agentId: string
  config?: {
    provider: string
    model: string
    temperature: number
    base_url?: string | null
  }
  isExpanded: boolean
  onToggle: () => void
  onSave: (data: ConfigFormData) => void
  onDelete: () => void
  saving: boolean
  message: { type: 'success' | 'error'; text: string } | null
}

export function AgentConfigCard({
  agentId,
  config,
  isExpanded,
  onToggle,
  onSave,
  onDelete,
  saving,
  message,
}: AgentConfigCardProps) {
  const meta = AGENT_META[agentId as keyof typeof AGENT_META] ?? { icon: '🤖', label: agentId }
  const [formProvider, setFormProvider] = useState(config?.provider ?? 'OpenAI')
  const [formModel, setFormModel] = useState(config?.model ?? '')
  const [formApiKey, setFormApiKey] = useState('')
  const [formBaseUrl, setFormBaseUrl] = useState(config?.base_url ?? '')
  const [formTemperature, setFormTemperature] = useState(config?.temperature ?? 0.7)
  const [showApiKey, setShowApiKey] = useState(false)

  const providerColor = PROVIDERS.find((p) => p.id === formProvider)?.color ?? '#9CA3AF'

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!formModel.trim()) return
    if (!formApiKey.trim() && !config) return
    onSave({
      agent: agentId,
      provider: formProvider,
      model: formModel,
      api_key: formApiKey,
      base_url: formBaseUrl,
      temperature: formTemperature,
    })
  }

  return (
    <div
      className={clsx(
        'group relative rounded-[30px] border-2 bg-white p-5 shadow-[0_18px_50px_rgba(30,43,40,0.06)] transition-all duration-300',
        isExpanded
          ? 'border-[var(--color-accent)] shadow-[0_24px_60px_rgba(199,107,79,0.15)]'
          : 'border-[var(--color-stroke)] hover:border-[var(--color-accent)]/40',
      )}
    >
      {/* Card Header — always visible, clickable to toggle */}
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full cursor-pointer items-start justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-12 w-12 items-center justify-center rounded-2xl text-2xl"
            style={{ backgroundColor: `${providerColor}18` }}
          >
            {meta.icon}
          </div>
          <div>
            <h3 className="text-base font-semibold text-[var(--color-ink)]">{meta.label}</h3>
            <p className="mt-0.5 text-xs text-[var(--color-muted)]">
              {config ? (
                <span className="inline-flex items-center gap-1.5">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ backgroundColor: providerColor }}
                  />
                  {config.provider} · {config.model}
                </span>
              ) : (
                '使用系统默认配置'
              )}
            </p>
          </div>
        </div>

        {/* Expand/Collapse chevron */}
        <div
          className={clsx(
            'mt-2 flex h-8 w-8 items-center justify-center rounded-xl border border-[var(--color-stroke)] bg-white text-[var(--color-muted)] transition-all duration-300',
            isExpanded && 'rotate-180 border-[var(--color-accent)] text-[var(--color-accent)]',
          )}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="transition-transform">
            <path d="M3 5L7 9L11 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>

      {/* Expanded Edit Form */}
      <div
        className={clsx(
          'overflow-hidden transition-all duration-300',
          isExpanded ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0',
        )}
      >
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Provider Brand Color Grid */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">
              Provider
            </label>
            <div className="grid grid-cols-4 gap-3">
              {PROVIDERS.map((provider) => {
                const isSelected = formProvider === provider.id
                return (
                  <button
                    key={provider.id}
                    type="button"
                    onClick={() => setFormProvider(provider.id)}
                    className={clsx(
                      'flex flex-col items-center gap-1.5 rounded-xl border-2 p-2 transition-all',
                      isSelected
                        ? 'border-transparent shadow-sm'
                        : 'border-[var(--color-stroke)] bg-white hover:border-[var(--color-muted)]',
                    )}
                  >
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold"
                      style={{
                        backgroundColor: provider.color,
                        color: provider.textColor,
                      }}
                    >
                      {provider.name.charAt(0)}
                    </div>
                    <span
                      className={clsx(
                        'text-center text-[10px] font-medium leading-tight',
                        isSelected ? 'text-[var(--color-ink)]' : 'text-[var(--color-muted)]',
                      )}
                    >
                      {provider.name}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Model */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">
              Model
            </label>
            <input
              type="text"
              value={formModel}
              onChange={(e) => setFormModel(e.target.value)}
              placeholder="例如：gpt-4o-mini"
              className="w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition placeholder:text-[var(--color-muted)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]"
            />
          </div>

          {/* API Key with show/hide toggle */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">
              API Key
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={formApiKey}
                onChange={(e) => setFormApiKey(e.target.value)}
                placeholder={config ? '（不填则保持不变）' : 'sk-...'}
                className="w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 pr-10 text-sm text-[var(--color-ink)] outline-none transition placeholder:text-[var(--color-muted)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]"
              />
              <button
                type="button"
                onClick={() => setShowApiKey((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              >
                {showApiKey ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Base URL */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">
              Base URL（可选）
            </label>
            <input
              type="text"
              value={formBaseUrl}
              onChange={(e) => setFormBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
              className="w-full rounded-2xl border border-[var(--color-stroke)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none transition placeholder:text-[var(--color-muted)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[rgba(199,107,79,0.14)]"
            />
          </div>

          {/* Temperature slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">
                Temperature
              </label>
              <span className="text-sm font-medium text-[var(--color-accent)]">{formTemperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={formTemperature}
              onChange={(e) => setFormTemperature(parseFloat(e.target.value))}
              className="w-full accent-[var(--color-accent)]"
            />
            <span className="block text-xs text-[var(--color-muted)]">控制输出的随机性，值越低越确定性</span>
          </div>

          {/* Message */}
          {message && (
            <div
              className={clsx(
                'rounded-2xl px-4 py-3 text-sm',
                message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700',
              )}
            >
              {message.text}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={saving || !formModel.trim() || (!formApiKey.trim() && !config)}
              className="inline-flex items-center justify-center rounded-full bg-[var(--color-accent)] px-6 py-3 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-55"
            >
              {saving ? '保存中...' : '保存'}
            </button>
            <button
              type="button"
              onClick={onToggle}
              className="inline-flex items-center justify-center rounded-full border border-[var(--color-stroke)] bg-white px-6 py-3 text-sm font-semibold text-[var(--color-ink)] transition hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
            >
              取消
            </button>
            {config && (
              <button
                type="button"
                onClick={onDelete}
                disabled={saving}
                className="inline-flex items-center justify-center rounded-full border border-red-200 bg-white px-6 py-3 text-sm font-semibold text-red-500 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-55"
              >
                删除配置
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Collapsed view: Edit button */}
      {!isExpanded && (
        <button
          type="button"
          onClick={onToggle}
          className="mt-4 w-full rounded-2xl border border-[var(--color-stroke)] bg-white py-2.5 text-sm font-semibold text-[var(--color-ink)] transition hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
        >
          {config ? '编辑配置' : '自定义配置'}
        </button>
      )}
    </div>
  )
}
