import type { ReactNode } from 'react'

type ProtectedRouteProps = {
  children: ReactNode
}

// TEMP: Bypassed for preview — restore auth check before committing
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  return <>{children}</>
}
