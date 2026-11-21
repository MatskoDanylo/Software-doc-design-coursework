import type { ProfileUpdate, User } from '../types/user'
import { apiRequest } from './client'

export const usersApi = {
  me: () => apiRequest<User>('/api/users/me'),
  updateMe: (data: ProfileUpdate) => apiRequest<User>('/api/users/me', { method: 'PATCH', body: data }),
}
