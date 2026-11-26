import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockApi, renderApp } from './test/utils'

describe('App', () => {
  it('renders the home page with guest actions', () => {
    renderApp('/')

    expect(screen.getByRole('heading', { name: 'Онлайн-кінотеатр' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Вхід' })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: 'Реєстрація' })).toHaveAttribute('href', '/register')
    expect(document.title).toBe('Cinema Platform')
  })

  it('shows the 404 page for unknown routes and names the tab', async () => {
    renderApp('/no-such-page')

    expect(screen.getByText('Сторінку не знайдено')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'На головну' })).toHaveAttribute('href', '/')
    await waitFor(() => expect(document.title).toBe('Сторінку не знайдено · Cinema Platform'))
  })

  it('names the tab after the opened page', async () => {
    mockApi({})
    renderApp('/catalog')

    await waitFor(() => expect(document.title).toBe('Каталог · Cinema Platform'))
  })
})
