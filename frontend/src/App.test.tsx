import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { renderApp } from './test/utils'

describe('App', () => {
  it('renders the home page with guest actions', () => {
    renderApp('/')

    expect(screen.getByRole('heading', { name: 'Онлайн-кінотеатр' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Вхід' })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: 'Реєстрація' })).toHaveAttribute('href', '/register')
  })
})
