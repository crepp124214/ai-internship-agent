import { clsx } from 'clsx'

export interface Provider {
  id: string
  name: string
  color: string
  textColor: string
}

export const PROVIDERS: Provider[] = [
  { id: 'OpenAI', name: 'OpenAI', color: '#10A37F', textColor: '#fff' },
  { id: 'Anthropic', name: 'Anthropic', color: '#D97706', textColor: '#fff' },
  { id: 'MiniMax', name: 'MiniMax', color: '#00C853', textColor: '#fff' },
  { id: 'DeepSeek', name: 'DeepSeek', color: '#7C3AED', textColor: '#fff' },
  { id: '智谱 AI', name: '智谱 AI', color: '#EF4444', textColor: '#fff' },
  { id: '通义千问', name: '通义千问', color: '#F59E0B', textColor: '#fff' },
  { id: 'Moonshot', name: 'Moonshot', color: '#4F46E5', textColor: '#fff' },
  { id: 'SiliconFlow', name: 'SiliconFlow', color: '#06B6D4', textColor: '#fff' },
]

interface ProviderSelectorProps {
  value: string
  onChange: (providerId: string) => void
}

export function ProviderSelector({ value, onChange }: ProviderSelectorProps) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {PROVIDERS.map((provider) => {
        const isSelected = value === provider.id
        return (
          <button
            key={provider.id}
            type="button"
            onClick={() => onChange(provider.id)}
            className={clsx(
              'flex flex-col items-center gap-2 rounded-2xl border-2 p-3 transition-all',
              isSelected
                ? 'border-transparent shadow-md'
                : 'border-[var(--color-stroke)] bg-white hover:border-[var(--color-muted)]',
            )}
          >
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl text-sm font-bold transition-transform"
              style={{
                backgroundColor: provider.color,
                color: provider.textColor,
                transform: isSelected ? 'scale(1.08)' : 'scale(1)',
              }}
            >
              {provider.name.charAt(0)}
            </div>
            <span
              className={clsx(
                'text-center text-xs font-medium leading-tight',
                isSelected ? 'text-[var(--color-ink)]' : 'text-[var(--color-muted)]',
              )}
            >
              {provider.name}
            </span>
          </button>
        )
      })}
    </div>
  )
}
