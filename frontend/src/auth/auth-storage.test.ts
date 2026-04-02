import { beforeEach, describe, expect, it } from 'vitest'

import { clearStoredToken, getStoredToken, setStoredToken } from './auth-storage'

describe('auth storage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('stores and reads bearer token', () => {
    setStoredToken('token-123')

    expect(getStoredToken()).toBe('token-123')
  })

  it('clears token', () => {
    setStoredToken('token-123')
    clearStoredToken()

    expect(getStoredToken()).toBeNull()
  })
})
