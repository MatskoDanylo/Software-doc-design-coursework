import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { describe, expect, it } from 'vitest'
import { apiRequest } from '../api/client'
import { tokens } from '../api/tokens'
import { callsTo, errorResponse, mockApi, signedInAs, testTokens, testUser } from '../test/utils'
import type { AuthContextValue } from './context'
import AuthProvider from './AuthProvider'
import { useAuth } from './useAuth'

const current: { auth: AuthContextValue | null } = { auth: null }

function Probe() {
  const auth = useAuth()
  useEffect(() => {
    current.auth = auth
  })
  return <p data-testid="status">{`${auth.status}:${auth.user?.email ?? '-'}`}</p>
}

function renderProvider() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <Probe />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

const status = () => screen.getByTestId('status').textContent

describe('AuthProvider', () => {
  it('starts as guest without a stored refresh token', () => {
    const fetchMock = mockApi({})
    renderProvider()

    expect(status()).toBe('guest:-')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('restores the session from the refresh token', async () => {
    mockApi(signedInAs(testUser))
    renderProvider()

    expect(status()).toBe('loading:-')
    expect(await screen.findByText('authenticated:viewer@example.com')).toBeInTheDocument()
  })

  it('falls back to guest when the profile cannot be loaded after refresh', async () => {
    localStorage.setItem('cinema.refresh_token', 'stored-refresh-token')
    mockApi({ 'POST /api/auth/refresh': testTokens, '/api/users/me': () => errorResponse(500, 'internal_error') })
    renderProvider()

    expect(await screen.findByText('guest:-')).toBeInTheDocument()
  })

  it('registers and signs the new user in', async () => {
    const fetchMock = mockApi({
      'POST /api/auth/register': { id: 1, email: testUser.email },
      'POST /api/auth/login': testTokens,
      '/api/users/me': testUser,
    })
    renderProvider()

    await act(() => current.auth!.register({ email: testUser.email, password: 'password123' }))

    expect(status()).toBe('authenticated:viewer@example.com')
    expect(JSON.parse(String(callsTo(fetchMock, 'POST', '/api/auth/login')[0].init?.body))).toEqual({
      email: testUser.email,
      password: 'password123',
    })
    expect(tokens.getRefresh()).toBe(testTokens.refresh_token)
  })

  it('logs out when the API reports that the session has expired', async () => {
    mockApi({
      ...signedInAs(testUser),
      '/api/favorites': () => errorResponse(401, 'invalid_token'),
    })
    renderProvider()
    await screen.findByText('authenticated:viewer@example.com')
    mockApi({
      'POST /api/auth/refresh': () => errorResponse(401, 'invalid_token'),
      '/api/favorites': () => errorResponse(401, 'invalid_token'),
    })

    await act(() => apiRequest('/api/favorites').catch(() => undefined))

    expect(status()).toBe('guest:-')
    expect(tokens.getRefresh()).toBeNull()
  })

  it('logout clears tokens and the user', async () => {
    mockApi(signedInAs(testUser))
    renderProvider()
    await screen.findByText('authenticated:viewer@example.com')

    act(() => current.auth!.logout())

    expect(status()).toBe('guest:-')
    expect(tokens.getAccess()).toBeNull()
  })
})
