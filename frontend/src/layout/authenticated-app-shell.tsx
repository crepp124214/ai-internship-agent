import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { Sidebar } from '../components/layout/Sidebar'
import { Topbar } from '../components/layout/Topbar'
import { CommandPalette } from '../components/layout/CommandPalette'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'

export function AuthenticatedAppShell() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)

  const handleOpenCommandPalette = () => {
    setCommandPaletteOpen(true)
  }

  const handleCloseCommandPalette = () => {
    setCommandPaletteOpen(false)
  }

  // Register global keyboard shortcuts
  useKeyboardShortcuts({
    onOpenCommandPalette: handleOpenCommandPalette,
  })

  return (
    <div className="flex h-screen bg-[var(--color-canvas)]">
      {/* Sidebar - Linear style */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Topbar */}
        <Topbar />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* Command Palette (global overlay) */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={handleCloseCommandPalette}
      />
    </div>
  )
}
