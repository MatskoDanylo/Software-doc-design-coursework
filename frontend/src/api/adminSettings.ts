import type { AppSettings, AppSettingsPayload } from '../types/settings'
import { apiRequest } from './client'

export const adminSettingsApi = {
  get: () => apiRequest<AppSettings>('/api/admin/settings'),
  update: (payload: AppSettingsPayload) => apiRequest<AppSettings>('/api/admin/settings', { method: 'PUT', body: payload }),
}

export const adminSettingsKeys = {
  all: ['admin', 'settings'] as const,
}
