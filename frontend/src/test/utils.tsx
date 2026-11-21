import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import App from '../App'
import type { TokenPair } from '../types/auth'
import type { User } from '../types/user'

export const testUser: User = {
  id: 1,
  email: 'viewer@example.com',
  role: 'user',
  created_at: '2026-11-21T10:00:00Z',
  profile: { display_name: 'Viewer', avatar_url: null, country: 'Ukraine' },
}

export const testTokens: TokenPair = {
  access_token: 'access-token',
  refresh_token: 'refresh-token',
  token_type: 'bearer',
}

export function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

export function mockApi(routes: Record<string, unknown>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const path = new URL(String(input), 'http://localhost').pathname
    if (!(path in routes)) return Response.json({ error: { code: 'not_found', message: path } }, { status: 404 })
    return Response.json(routes[path])
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
