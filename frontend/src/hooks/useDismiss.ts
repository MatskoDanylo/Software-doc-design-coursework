import { useEffect, type RefObject } from 'react'

export function useDismiss(ref: RefObject<HTMLElement | null>, active: boolean, onDismiss: () => void): void {
  useEffect(() => {
    if (!active) return
    const handlePointer = (event: MouseEvent) => {
      if (event.target instanceof Node && !ref.current?.contains(event.target)) onDismiss()
    }
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDismiss()
    }
    document.addEventListener('mousedown', handlePointer)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handlePointer)
      document.removeEventListener('keydown', handleKey)
    }
  }, [ref, active, onDismiss])
}
