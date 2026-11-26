import type { Subscription } from '../types/user'
import { apiRequest } from './client'

export const subscriptionsApi = {
  cancel: () => apiRequest<Subscription>('/api/subscriptions/cancel', { method: 'POST' }),
}
