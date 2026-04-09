import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

interface KeyboardShortcutHandlers {
  onOpenCommandPalette?: () => void
  enabled?: boolean
}

export function useKeyboardShortcuts({
  onOpenCommandPalette,
  enabled = true,
}: KeyboardShortcutHandlers = {}) {
  const navigate = useNavigate()
  const gKeyPressed = useRef(false)
  const gKeyTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input/textarea
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
      const modifierKey = isMac ? e.metaKey : e.ctrlKey

      // ⌘K or Ctrl+K: Open command palette
      if (modifierKey && e.key === 'k') {
        e.preventDefault()
        onOpenCommandPalette?.()
        return
      }

      // G + D: Dashboard (after pressing G, you have 500ms to press the next key)
      if (e.key === 'g' && !e.metaKey && !e.ctrlKey) {
        if (gKeyPressed.current) {
          // Already in G-sequence mode, pressing G again cancels the mode
          gKeyPressed.current = false
          clearTimeout(gKeyTimeout.current)
          return
        }
        gKeyPressed.current = true
        clearTimeout(gKeyTimeout.current)
        gKeyTimeout.current = setTimeout(() => {
          gKeyPressed.current = false
        }, 500)
        return
      }

      // Handle second key in G-sequence
      if (gKeyPressed.current) {
        gKeyPressed.current = false
        clearTimeout(gKeyTimeout.current)

        switch (e.key.toLowerCase()) {
          case 'd':
            e.preventDefault()
            navigate('/')
            break
          case 'j':
            e.preventDefault()
            navigate('/jobs-explore')
            break
          case 'r':
            e.preventDefault()
            navigate('/resume')
            break
          case 'i':
            e.preventDefault()
            navigate('/interview')
            break
          default:
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      clearTimeout(gKeyTimeout.current)
    }
  }, [enabled, navigate, onOpenCommandPalette])
}
