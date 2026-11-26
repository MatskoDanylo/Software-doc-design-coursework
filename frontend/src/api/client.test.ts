import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { callsTo, errorResponse, mockApi, testTokens } from '../test/utils'
import { ApiError, apiDownload, apiRequest, apiUrl, onSessionExpired, refreshSession } from './client'
import { tokens } from './tokens'

const fresh = { ...testTokens, access_token: 'fresh-access', refresh_token: 'fresh-refresh' }

function headersOf(init?: RequestInit): Record<string, string> {
  return (init?.headers ?? {}) as Record<string, string>
}

describe('apiRequest', () => {
  beforeEach(() => tokens.save(testTokens))
  afterEach(() => onSessionExpired(null))

  it('sends JSON with the access token', async () => {
    const fetchMock = mockApi({ 'POST /api/things': { ok: true } })

    await expect(apiRequest('/api/things', { method: 'POST', body: { a: 1 } })).resolves.toEqual({ ok: true })

    const [{ init }] = callsTo(fetchMock, 'POST', '/api/things')
    expect(init?.body).toBe('{"a":1}')
    expect(headersOf(init)).toMatchObject({
      Authorization: 'Bearer access-token',
      'Content-Type': 'application/json',
    })
  })

  it('lets the browser set the multipart boundary for FormData', async () => {
    const fetchMock = mockApi({ 'POST /api/upload': { ok: true } })
    const form = new FormData()

    await apiRequest('/api/upload', { method: 'POST', body: form })

    const [{ init }] = callsTo(fetchMock, 'POST', '/api/upload')
    expect(init?.body).toBe(form)
    expect(headersOf(init)).not.toHaveProperty('Content-Type')
  })

  it('does not send the token for public requests', async () => {
    const fetchMock = mockApi({ '/api/plans': [] })

    await apiRequest('/api/plans', { auth: false })

    expect(headersOf(callsTo(fetchMock, 'GET', '/api/plans')[0].init)).not.toHaveProperty('Authorization')
  })

  it('returns null for 204 No Content', async () => {
    mockApi({ 'DELETE /api/favorites/1': () => new Response(null, { status: 204 }) })

    await expect(apiRequest('/api/favorites/1', { method: 'DELETE' })).resolves.toBeNull()
  })

  it('turns the API error envelope into ApiError', async () => {
    const details = [{ loc: ['body', 'email'], msg: 'bad', type: 'value_error' }]
    mockApi({ 'POST /api/auth/register': () => errorResponse(422, 'validation_error', details) })

    const error = await apiRequest('/api/auth/register', { method: 'POST', body: {} }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 422, code: 'validation_error', details })
  })

  it('falls back to http_error when the body is not an API error', async () => {
    mockApi({ '/api/broken': () => new Response('<html>', { status: 502, statusText: 'Bad Gateway' }) })

    await expect(apiRequest('/api/broken')).rejects.toMatchObject({
      status: 502,
      code: 'http_error',
      message: 'Bad Gateway',
    })
  })

  it('reports an unreachable server as network_error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(apiRequest('/api/titles')).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })

  it('refreshes an expired access token once and retries the request', async () => {
    const fetchMock = mockApi({
      'POST /api/auth/refresh': fresh,
      '/api/users/me': (_url: URL, init?: RequestInit) =>
        headersOf(init).Authorization === 'Bearer fresh-access'
          ? Response.json({ id: 1 })
          : errorResponse(401, 'invalid_token'),
    })

    const results = await Promise.all([apiRequest('/api/users/me'), apiRequest('/api/users/me')])

    expect(results).toEqual([{ id: 1 }, { id: 1 }])
    expect(callsTo(fetchMock, 'POST', '/api/auth/refresh')).toHaveLength(1)
    expect(tokens.getAccess()).toBe('fresh-access')
    expect(tokens.getRefresh()).toBe('fresh-refresh')
  })

  it('ends the session when the refresh token is rejected', async () => {
    const expired = vi.fn()
    onSessionExpired(expired)
    mockApi({
      'POST /api/auth/refresh': () => errorResponse(401, 'invalid_token'),
      '/api/users/me': () => errorResponse(401, 'invalid_token'),
    })

    await expect(apiRequest('/api/users/me')).rejects.toMatchObject({ status: 401 })

    expect(expired).toHaveBeenCalledOnce()
    expect(tokens.getAccess()).toBeNull()
    expect(tokens.getRefresh()).toBeNull()
  })
})

describe('refreshSession', () => {
  it('does nothing without a stored refresh token', async () => {
    const fetchMock = mockApi({})

    await expect(refreshSession()).resolves.toBe(false)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('keeps the refresh token when the server is unreachable', async () => {
    tokens.save(testTokens)
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(refreshSession()).resolves.toBe(false)
    expect(tokens.getRefresh()).toBe('refresh-token')
  })
})

describe('apiDownload', () => {
  beforeEach(() => tokens.save(testTokens))

  it('returns the blob with the server-provided file name', async () => {
    mockApi({
      '/api/admin/reports/popular-titles/export': () =>
        new Response('a;b', { headers: { 'Content-Disposition': 'attachment; filename="popular.csv"' } }),
    })

    const file = await apiDownload('/api/admin/reports/popular-titles/export')

    expect(file.filename).toBe('popular.csv')
    await expect(file.blob.text()).resolves.toBe('a;b')
  })

  it('returns null file name when the header is missing and rejects errors', async () => {
    mockApi({
      '/api/export/ok': () => new Response('x'),
      '/api/export/forbidden': () => errorResponse(403, 'forbidden'),
    })

    expect((await apiDownload('/api/export/ok')).filename).toBeNull()
    await expect(apiDownload('/api/export/forbidden')).rejects.toMatchObject({ code: 'forbidden' })
  })
})

describe('apiUrl', () => {
  it('keeps absolute URLs and prefixes relative API paths', () => {
    expect(apiUrl('https://cdn.example.com/a.m3u8')).toBe('https://cdn.example.com/a.m3u8')
    expect(apiUrl('/api/titles')).toMatch(/\/api\/titles$/)
  })
})
