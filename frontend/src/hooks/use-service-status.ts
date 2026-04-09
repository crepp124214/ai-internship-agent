import { create } from 'zustand'

export type ServiceStatus = 'idle' | 'checking' | 'ready' | 'error'

interface ServiceState {
  status: ServiceStatus
  readyError: string | null
  lastChecked: Date | null
  apiBaseUrl: string

  // Actions
  setStatus: (status: ServiceStatus) => void
  setReadyError: (error: string | null) => void
  checkConnectivity: () => Promise<void>
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export const useServiceStatus = create<ServiceState>((set, get) => ({
  status: 'idle',
  readyError: null,
  lastChecked: null,
  apiBaseUrl,

  setStatus: (status) => set({ status }),

  setReadyError: (readyError) => set({ readyError }),

  checkConnectivity: async () => {
    const { apiBaseUrl } = get()
    
    set({ status: 'checking', readyError: null })

    try {
      // Probe /ready endpoint at root level
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)

      // Try the backend /ready endpoint
      const response = await fetch(`${apiBaseUrl}/ready`, {
        method: 'GET',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
      })

      clearTimeout(timeoutId)

      if (response.ok) {
        set({
          status: 'ready',
          readyError: null,
          lastChecked: new Date(),
        })
      } else {
        set({
          status: 'error',
          readyError: `服务暂不可用 (${response.status})`,
          lastChecked: new Date(),
        })
      }
    } catch (error) {
      // Network error or timeout
      const errorMessage = error instanceof Error 
        ? error.message 
        : '无法连接到后端服务'
      
      set({
        status: 'error',
        readyError: errorMessage,
        lastChecked: new Date(),
      })
    }
  },
}))