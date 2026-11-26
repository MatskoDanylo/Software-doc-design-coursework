import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import RouteErrorBoundary from './RouteErrorBoundary'

function Broken({ message }: { message: string }): never {
  throw new Error(message)
}

function renderBoundary(message: string) {
  return render(
    <MemoryRouter>
      <RouteErrorBoundary>
        <Broken message={message} />
      </RouteErrorBoundary>
    </MemoryRouter>,
  )
}

describe('RouteErrorBoundary', () => {
  beforeEach(() => vi.spyOn(console, 'error').mockImplementation(() => undefined))
  afterEach(() => vi.restoreAllMocks())

  it('replaces a crashed page with a recoverable message', () => {
    renderBoundary('Cannot read properties of undefined')

    expect(screen.getByRole('alert')).toHaveTextContent('Щось пішло не так')
    expect(screen.getByRole('button', { name: 'Оновити сторінку' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'На головну' })).toHaveAttribute('href', '/')
  })

  it('explains a failed lazy chunk as a new app version', () => {
    renderBoundary('Failed to fetch dynamically imported module: /assets/WatchPage.js')

    expect(screen.getByText(/вийшла нова версія/)).toBeInTheDocument()
  })

  it('renders children when nothing is broken', () => {
    render(
      <MemoryRouter>
        <RouteErrorBoundary>
          <p>Сторінка</p>
        </RouteErrorBoundary>
      </MemoryRouter>,
    )

    expect(screen.getByText('Сторінка')).toBeInTheDocument()
  })
})
