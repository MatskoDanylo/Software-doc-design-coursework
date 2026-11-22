import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi, type Mock } from 'vitest'
import App from '../App'
import type { TokenPair } from '../types/auth'
import type { User } from '../types/user'
import LocationProbe from './LocationProbe'

export const testUser: User = {
  id: 1,
  email: 'viewer@example.com',
  role: 'user',
  created_at: '2026-11-21T10:00:00Z',
  profile: { display_name: 'Viewer', avatar_url: null, country: 'Ukraine' },
}

export const testAdmin: User = {
  ...testUser,
  id: 2,
  email: 'admin@example.com',
  role: 'admin',
  profile: { display_name: 'Admin', avatar_url: null, country: 'Ukraine' },
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
      <LocationProbe />
    </MemoryRouter>,
  )
}

export function currentUrl(): URL {
  return new URL(screen.getByTestId('location').textContent ?? '/', 'http://localhost')
}

export function signedInAs(user: User): Record<string, unknown> {
  localStorage.setItem('cinema.refresh_token', 'stored-refresh-token')
  return { 'POST /api/auth/refresh': testTokens, '/api/users/me': user }
}

export type RouteHandler = (url: URL, init?: RequestInit) => Response
type FetchMock = Mock<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>

function isHandler(value: unknown): value is RouteHandler {
  return typeof value === 'function'
}

export function mockApi(routes: Record<string, unknown>): FetchMock {
  const fetchMock: FetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost')
    const key = [`${init?.method ?? 'GET'} ${url.pathname}`, url.pathname].find((candidate) => candidate in routes)
    if (key === undefined) {
      return Response.json({ error: { code: 'not_found', message: url.pathname } }, { status: 404 })
    }
    const route = routes[key]
    return isHandler(route) ? route(url, init) : Response.json(route)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export function callsTo(fetchMock: FetchMock, method: string, path: string) {
  return fetchMock.mock.calls
    .map(([input, init]) => ({ url: new URL(String(input), 'http://localhost'), init }))
    .filter(({ url, init }) => url.pathname === path && (init?.method ?? 'GET') === method)
}

export function errorResponse(status: number, code: string, details: unknown[] = []): Response {
  return Response.json({ error: { code, message: code, details } }, { status })
}
