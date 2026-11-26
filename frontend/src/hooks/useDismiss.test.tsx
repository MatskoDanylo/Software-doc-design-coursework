import { fireEvent, render, screen } from '@testing-library/react'
import { useRef } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useDismiss } from './useDismiss'

function Popover({ active, onDismiss }: { active: boolean; onDismiss: () => void }) {
  const ref = useRef<HTMLDivElement>(null)
  useDismiss(ref, active, onDismiss)
  return (
    <div>
      <div ref={ref}>
        <button type="button">inside</button>
      </div>
      <button type="button">outside</button>
    </div>
  )
}

describe('useDismiss', () => {
  it('dismisses on outside click and Escape, not on inside click', () => {
    const onDismiss = vi.fn()
    render(<Popover active onDismiss={onDismiss} />)

    fireEvent.mouseDown(screen.getByRole('button', { name: 'inside' }))
    expect(onDismiss).not.toHaveBeenCalled()

    fireEvent.mouseDown(screen.getByRole('button', { name: 'outside' }))
    fireEvent.keyDown(document, { key: 'Escape' })
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(onDismiss).toHaveBeenCalledTimes(2)
  })

  it('ignores events while inactive and after unmount', () => {
    const onDismiss = vi.fn()
    const { rerender, unmount } = render(<Popover active={false} onDismiss={onDismiss} />)

    fireEvent.mouseDown(document.body)
    rerender(<Popover active onDismiss={onDismiss} />)
    unmount()
    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onDismiss).not.toHaveBeenCalled()
  })
})
