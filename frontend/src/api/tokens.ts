import type { TokenPair } from '../types/auth'

const REFRESH_TOKEN_KEY = 'cinema.refresh_token'

let accessToken: string | null = null

export const tokens = {
  getAccess(): string | null {
    return accessToken
  },
  getRefresh(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  save(pair: TokenPair): void {
    accessToken = pair.access_token
    localStorage.setItem(REFRESH_TOKEN_KEY, pair.refresh_token)
  },
  clear(): void {
    accessToken = null
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}
