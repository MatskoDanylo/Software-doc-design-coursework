export interface RegisterRequest {
  email: string
  password: string
  display_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RefreshRequest {
  refresh_token: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}
