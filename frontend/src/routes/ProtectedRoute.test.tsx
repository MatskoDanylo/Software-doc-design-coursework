import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockApi, renderApp, testTokens, testUser } from '../test/utils'

const profileHeading = { name: 'Редагування профілю' }
const loginHeading = { name: 'Вхід' }

describe('ProtectedRoute', () => {
  it('redirects to /login when there is no token', async () => {
    const fetchMock = mockApi({})
    renderApp('/profile')

    expect(await screen.findByRole('heading', loginHeading)).toBeInTheDocument()
    expect(screen.queryByRole('heading', profileHeading)).not.toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('returns to the requested page after login', async () => {
    mockApi({ '/api/auth/login': testTokens, '/api/users/me': testUser })
    renderApp('/profile')

    fireEvent.change(await screen.findByLabelText('Email'), { target: { value: testUser.email } })
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'secret123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Увійти' }))

    expect(await screen.findByRole('heading', profileHeading)).toBeInTheDocument()
  })

  it('restores the session from the stored refresh token', async () => {
    localStorage.setItem('cinema.refresh_token', 'stored-refresh-token')
    const fetchMock = mockApi({ '/api/auth/refresh': testTokens, '/api/users/me': testUser })
    renderApp('/profile')

    expect(await screen.findByRole('heading', profileHeading)).toBeInTheDocument()
    const meCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/api/users/me'))
    expect(meCall?.[1]?.headers).toMatchObject({ Authorization: `Bearer ${testTokens.access_token}` })
  })
})
