// frontend/src/pages/components/FloatingToolbar.tsx
import { useEffect, useRef, useState } from 'react'

interface FloatingToolbarProps {
  targetRef: React.RefObject<HTMLElement | null>
  onOptimize: (selectedText: string) => void
  onSummarize: (selectedText: string) => void
  onExplain: (selectedText: string) => void
}

export function FloatingToolbar({
  targetRef,
  onOptimize,
  onSummarize,
  onExplain,
}: FloatingToolbarProps) {
  const [visible, setVisible] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const [selectedText, setSelectedText] = useState('')
  const toolbarRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = window.getSelection()
      if (!selection || selection.isCollapsed || !selection.toString().trim()) {
        setVisible(false)
        return
      }

      const targetEl = targetRef.current
      if (!targetEl) return

      // Check if selection is within target element
      const range = selection.getRangeAt(0)
      if (!targetEl.contains(range.commonAncestorContainer)) {
        setVisible(false)
        return
      }

      const text = selection.toString().trim()
      if (text.length < 2) {
        setVisible(false)
        return
      }

      const rect = range.getBoundingClientRect()
      setSelectedText(text)
      setPosition({
        top: rect.top + window.scrollY - 48,
        left: rect.left + window.scrollX + rect.width / 2,
      })
      setVisible(true)
    }

    document.addEventListener('mouseup', handleSelectionChange)
    document.addEventListener('keyup', handleSelectionChange)

    return () => {
      document.removeEventListener('mouseup', handleSelectionChange)
      document.removeEventListener('keyup', handleSelectionChange)
    }
  }, [targetRef])

  const handleAction = (action: (text: string) => void) => {
    action(selectedText)
    setVisible(false)
    window.getSelection()?.removeAllRanges()
  }

  if (!visible) return null

  return (
    <div
      ref={toolbarRef}
      className="fixed z-50 flex items-center gap-1 rounded-[8px] border border-white/10 bg-[#171717] px-2 py-1.5 shadow-[0_8px_32px_rgba(30,43,40,0.18)]"
      style={{ top: position.top, left: position.left, transform: 'translateX(-50%)' }}
    >
      <button
        type="button"
        onClick={() => handleAction(onOptimize)}
        className="inline-flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/10"
        title="优化措辞"
      >
        <span>✨</span>
        <span>优化</span>
      </button>
      <div className="h-4 w-px bg-white/20" />
      <button
        type="button"
        onClick={() => handleAction(onSummarize)}
        className="inline-flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/10"
        title="生成摘要"
      >
        <span>📝</span>
        <span>摘要</span>
      </button>
      <div className="h-4 w-px bg-white/20" />
      <button
        type="button"
        onClick={() => handleAction(onExplain)}
        className="inline-flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/10"
        title="解释内容"
      >
        <span>💬</span>
        <span>解释</span>
      </button>
    </div>
  )
}
