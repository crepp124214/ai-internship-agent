import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { WorkspaceShell } from '../page-primitives'
import { getUserLlmConfigs, type UserLlmConfig } from '../../lib/api'
import { getStoredToken } from '../../auth/auth-storage'

// 管理入口卡片
const MANAGEMENT_CARDS = [
  {
    id: 'resumes',
    icon: '📄',
    title: '简历管理',
    description: '管理多版本简历',
    path: '/settings/resumes',
  },
  {
    id: 'jobs',
    icon: '💼',
    title: '岗位管理',
    description: '跟踪求职进度',
    path: '/settings/jobs',
  },
  {
    id: 'interviews',
    icon: '🎤',
    title: '面试记录',
    description: '查看练习历史',
    path: '/settings/interviews',
  },
]

// Agent 配置入口卡片
const AGENT_CONFIG_ENTRY = {
  id: 'agent-config',
  icon: '🤖',
  title: 'Agent 配置',
  description: '自定义各 Agent 的 AI 行为',
  path: '/settings/agent-config',
}

/**
 * 全局配置区 - 左侧面板
 */
function GlobalConfigPanel({ configs }: { configs: UserLlmConfig[] }) {
  // 从配置中提取全局 provider 和 model
  const sharedProvider = configs[0]?.provider ?? '未设置'
  const sharedModel = configs[0]?.model ?? '未设置'
  const configuredCount = configs.length

  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <span className="text-xl">⚙️</span>
        <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">全局配置</h3>
      </div>

      <div className="mb-6 space-y-3">
        <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-3">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Provider</span>
          <span className="text-sm font-medium text-[var(--color-ink)]">{sharedProvider}</span>
        </div>
        <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-3">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">Model</span>
          <span className="text-sm font-medium text-[var(--color-ink)]">{sharedModel}</span>
        </div>
        <div className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-3">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">已配置</span>
          <span className="text-sm font-medium text-[var(--color-ink)]">{configuredCount} / 3 个 Agent</span>
        </div>
      </div>
    </div>
  )
}

/**
 * 系统状态区 - 右侧面板
 */
function SystemStatusPanel({ configs }: { configs: UserLlmConfig[] }) {
  // 转换为状态展示
  const agentStatuses = [
    { id: 'resume_agent', label: '简历 Agent', config: configs.find((c) => c.agent === 'resume_agent') },
    { id: 'job_agent', label: '岗位 Agent', config: configs.find((c) => c.agent === 'job_agent') },
    { id: 'interview_agent', label: '面试 Agent', config: configs.find((c) => c.agent === 'interview_agent') },
  ]

  const configuredCount = agentStatuses.filter((a) => a.config).length

  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <span className="text-xl">📊</span>
        <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">系统状态</h3>
      </div>

      <div className="mb-4 space-y-2">
        {agentStatuses.map((agent) => (
          <div
            key={agent.id}
            className="flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-2.5"
          >
            <span className="text-sm font-medium text-[var(--color-ink)]">{agent.label}</span>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${
                agent.config
                  ? 'bg-green-50 text-green-700'
                  : 'bg-gray-50 text-gray-500'
              }`}
            >
              {agent.config ? '可用' : '未配置'}
            </span>
          </div>
        ))}
      </div>

      {/* 连接状态汇总 */}
      <div className="rounded-xl bg-[var(--color-surface)] px-4 py-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--color-muted)]">连接状态</span>
          <span className="text-sm font-medium text-green-700">
            {configuredCount > 0 ? `${configuredCount} 个 Agent 已配置` : '未配置'}
          </span>
        </div>
      </div>
    </div>
  )
}

/**
 * Agent 配置入口 - 作为次级入口
 */
function AgentConfigEntry() {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate(AGENT_CONFIG_ENTRY.path)}
      className="group flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-white/60 px-4 py-3 text-left transition-colors hover:bg-white hover:border-[var(--color-accent)]/30"
    >
      <span className="text-xl">{AGENT_CONFIG_ENTRY.icon}</span>
      <div className="flex-1">
        <p className="text-sm font-medium text-[var(--color-ink-primary)]">{AGENT_CONFIG_ENTRY.title}</p>
        <p className="text-xs text-[var(--color-ink-tertiary)]">{AGENT_CONFIG_ENTRY.description}</p>
      </div>
      <span className="text-sm text-[var(--color-ink-tertiary)] transition-transform group-hover:translate-x-1">
        →
      </span>
    </button>
  )
}

/**
 * 管理入口区 - 第三层
 * 只包含按钮列表，外层包装已在主组件提供
 */
function ManagementEntries() {
  const navigate = useNavigate()

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {MANAGEMENT_CARDS.map((card) => (
        <button
          key={card.id}
          onClick={() => navigate(card.path)}
          className="group flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-white/60 px-4 py-3 text-left transition-colors hover:bg-white hover:border-[var(--color-accent)]/30"
        >
          <span className="text-xl">{card.icon}</span>
          <div className="flex-1">
            <p className="text-sm font-medium text-[var(--color-ink-primary)]">{card.title}</p>
            <p className="text-xs text-[var(--color-ink-tertiary)]">{card.description}</p>
          </div>
          <span className="text-sm text-[var(--color-ink-tertiary)] transition-transform group-hover:translate-x-1">
            →
          </span>
        </button>
      ))}
    </div>
  )
}

/**
 * 统一导入面板内部组件 - 被第二层包装
 */
function UnifiedImportPanelInner() {
  const [activeTab, setActiveTab] = useState<'resume' | 'jd'>('resume')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const endpoint = activeTab === 'resume'
        ? '/api/v1/import/resume'
        : '/api/v1/import/jds'

      const token = getStoredToken()
      const headers: Record<string, string> = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers,
      })

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(String(err))
    } finally {
      setUploading(false)
    }
  }

  const handleTabChange = (tab: 'resume' | 'jd') => {
    setActiveTab(tab)
    setFile(null)
    setResult(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const selectedFileName = file ? file.name : ''

  return (
    <>
      <div className="mb-4 flex gap-2">
        <button
          className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'resume'
              ? 'bg-[var(--color-accent)] text-white'
              : 'bg-white text-[var(--color-ink-secondary)] hover:bg-[var(--color-border)]'
          }`}
          onClick={() => handleTabChange('resume')}
        >
          导入简历
        </button>
        <button
          className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'jd'
              ? 'bg-[var(--color-accent)] text-white'
              : 'bg-white text-[var(--color-ink-secondary)] hover:bg-[var(--color-border)]'
          }`}
          onClick={() => handleTabChange('jd')}
        >
          导入岗位
        </button>
      </div>

      <div className="mb-4">
        <div className="flex items-center gap-3">
          <div className="relative inline-flex overflow-hidden rounded-lg border border-[var(--color-border)] bg-white">
            <span className="pointer-events-none px-4 py-2 text-sm font-medium text-[var(--color-ink-primary)]">
              选择文件
            </span>
            <input
              ref={fileInputRef}
              type="file"
              accept={activeTab === 'resume' ? '.pdf,.docx' : '.csv,.xlsx'}
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              aria-label="选择文件"
              className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            />
          </div>
          <span className="text-sm text-[var(--color-ink-secondary)]">
            {selectedFileName || '未选择文件'}
          </span>
        </div>
        <p className="mt-2 text-sm text-[var(--color-ink-secondary)]">
          点击“选择文件”后，从本地文件夹中选择要导入的文件
        </p>
        <p className="mt-1 text-xs text-[var(--color-ink-tertiary)]">
          {activeTab === 'resume' ? '支持 PDF、DOCX 格式' : '支持 CSV、Excel 格式'}
        </p>
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full rounded-lg bg-[var(--color-accent)] py-2 px-4 text-sm font-semibold text-white transition-colors hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {uploading ? '上传中...' : '上传'}
      </button>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {result && (
        <div className={`mt-4 rounded-lg p-3 ${
          result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {result.success ? (
            <div>
              <p className="font-semibold">导入成功！</p>
              {activeTab === 'resume' ? (
                <p className="text-sm">简历 ID: {result.resume_id}</p>
              ) : (
                <p className="text-sm">
                  成功导入 {result.imported}/{result.total} 条
                  {result.failed > 0 && `（失败 ${result.failed} 条）`}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm">导入失败：{result.detail || result.error}</p>
          )}
        </div>
      )}
    </>
  )
}

export function SettingsPage() {
  // 获取 LLM 配置状态
  const configsQuery = useQuery({
    queryKey: ['user-llm-configs'],
    queryFn: getUserLlmConfigs,
    // 失败时使用空数组，保持页面可渲染
    retry: false,
  })

  const configs = configsQuery.data ?? []

  return (
    <WorkspaceShell
      title="设置中心"
      subtitle="系统控制中心"
    >
      <div className="flex flex-col gap-8">
        {/* 第一层：配置与状态并列 - 视觉重量更稳定 */}
        <div className="grid gap-6 lg:grid-cols-2">
          <GlobalConfigPanel configs={configs} />
          <SystemStatusPanel configs={configs} />
        </div>

        {/* 第二层：工具面板型 - 比第一层更轻 */}
        <div className="rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-panel)] p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-lg">🛠️</span>
            <h3 className="text-base font-semibold text-[var(--color-ink-primary)]">工具导入</h3>
          </div>
          <UnifiedImportPanelInner />
        </div>

        {/* 第三层：管理入口 - 进一步退到次级 */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-lg">📁</span>
            <h3 className="text-base font-semibold text-[var(--color-ink-secondary)]">数据管理</h3>
          </div>
          <ManagementEntries />
        </div>

        {/* 第四层：Agent 配置入口 - 作为次级入口 */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-lg">🤖</span>
            <h3 className="text-base font-semibold text-[var(--color-ink-secondary)]">Agent 配置</h3>
          </div>
          <AgentConfigEntry />
        </div>
      </div>
    </WorkspaceShell>
  )
}
