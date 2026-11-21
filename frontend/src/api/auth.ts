import type { LoginRequest, RegisterRequest, TokenPair } from '../types/auth'
import type { User } from '../types/user'
import { apiRequest } from './client'

export const authApi = {
  register: (data: RegisterRequest) =>
    apiRequest<User>('/api/auth/register', { method: 'POST', body: data, auth: false }),
  login: (data: LoginRequest) =>
    apiRequest<TokenPair>('/api/auth/login', { method: 'POST', body: data, auth: false }),
}
