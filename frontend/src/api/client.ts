import type { TokenPair } from '../types/auth'
import type { ApiErrorBody, ApiErrorDetail } from '../types/errors'
import { tokens } from './tokens'

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

export function apiUrl(path: string): string {
  return /^https?:\/\//.test(path) ? path : `${API_URL}${path}`
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  auth?: boolean
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: ApiErrorDetail[]

  constructor(status: number, code: string, message: string, details: ApiErrorDetail[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

let sessionExpiredHandler: (() => void) | null = null
let refreshInFlight: Promise<boolean> | null = null

export function onSessionExpired(handler: (() => void) | null): void {
  sessionExpiredHandler = handler
}

function isErrorBody(data: unknown): data is ApiErrorBody {
  return (
    typeof data === 'object' &&
    data !== null &&
    'error' in data &&
    typeof data.error === 'object' &&
    data.error !== null &&
    'code' in data.error &&
    'message' in data.error
  )
}

async function send(path: string, method: HttpMethod, body: unknown, accessToken: string | null): Promise<Response> {
  const isForm = body instanceof FormData
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  try {
    return await fetch(apiUrl(path), {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'network_error', 'Network error')
  }
}

async function parse<T>(response: Response): Promise<T> {
  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    if (isErrorBody(data)) {
      const { code, message, details } = data.error
      throw new ApiError(response.status, code, message, details)
    }
    throw new ApiError(response.status, 'http_error', response.statusText || 'Request failed')
  }
  return data as T
}

async function requestNewTokens(): Promise<boolean> {
  const refreshToken = tokens.getRefresh()
  if (!refreshToken) return false

  try {
    const response = await send('/api/auth/refresh', 'POST', { refresh_token: refreshToken }, null)
    tokens.save(await parse<TokenPair>(response))
    return true
  } catch (error) {
    if (error instanceof ApiError && error.status !== 0) tokens.clear()
    return false
  }
}

export function refreshSession(): Promise<boolean> {
  refreshInFlight ??= requestNewTokens().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

export async function apiRequest<T>(path: string, { method = 'GET', body, auth = true }: RequestOptions = {}): Promise<T> {
  let response = await send(path, method, body, auth ? tokens.getAccess() : null)

  if (auth && response.status === 401) {
    if (await refreshSession()) {
      response = await send(path, method, body, tokens.getAccess())
    }
    if (response.status === 401) {
      tokens.clear()
      sessionExpiredHandler?.()
    }
  }

  return parse<T>(response)
}
