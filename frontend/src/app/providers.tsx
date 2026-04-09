import type { PropsWithChildren } from 'react'
import { useEffect } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'

import { AuthProvider } from '../auth/auth-provider'
import { useServiceStatus } from '../hooks/use-service-status'
import { queryClient } from '../lib/query-client'

function ServiceStatusChecker({ children }: PropsWithChildren) {
  const { status, checkConnectivity } = useServiceStatus()

  useEffect(() => {
    // Check connectivity on app startup
    if (status === 'idle') {
      void checkConnectivity()
    }
  }, [status, checkConnectivity])

  return <>{children}</>
}

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <ServiceStatusChecker>
        <AuthProvider>{children}</AuthProvider>
      </ServiceStatusChecker>
    </QueryClientProvider>
  )
}
