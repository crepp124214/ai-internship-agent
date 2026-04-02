const TOKEN_STORAGE_KEY = 'ai-internship-agent.token'
const REFRESH_TOKEN_STORAGE_KEY = 'ai-internship-agent.refresh_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

// Store both access and refresh tokens together
export function setStoredTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refresh)
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

export function clearStoredTokens(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
}
