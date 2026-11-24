import type { AppNotification, NotificationInbox } from '../types/notification'
import { apiRequest } from './client'

export const NOTIFICATIONS_LIMIT = 10

export const notificationsApi = {
  inbox: () => apiRequest<NotificationInbox>(`/api/notifications?limit=${NOTIFICATIONS_LIMIT}`),
  markRead: (id: number) => apiRequest<AppNotification>(`/api/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () => apiRequest<{ updated: number }>('/api/notifications/read-all', { method: 'POST' }),
}

export const notificationsKeys = {
  inbox: ['notifications'] as const,
}
