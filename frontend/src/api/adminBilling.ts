import type {
  AdminPayment,
  AdminPaymentFilters,
  AdminPaymentPage,
  ResolveOutcome,
  SubscriptionChange,
} from '../types/adminBilling'
import type { Account, Subscription } from '../types/user'
import { apiRequest } from './client'

export const ADMIN_PAYMENTS_PAGE_SIZE = 20
export const ADMIN_USERS_PAGE_SIZE = 20

function paymentsQuery({ status, page }: AdminPaymentFilters): string {
  const params = new URLSearchParams({ page: String(page), page_size: String(ADMIN_PAYMENTS_PAGE_SIZE) })
  if (status) params.set('status', status)
  return params.toString()
}

export const adminBillingApi = {
  payments: (filters: AdminPaymentFilters) => apiRequest<AdminPaymentPage>(`/api/admin/payments?${paymentsQuery(filters)}`),
  resolve: (paymentId: number, outcome: ResolveOutcome) =>
    apiRequest<AdminPayment>(`/api/admin/payments/${paymentId}/resolve`, { method: 'POST', body: { outcome } }),
  users: (page: number) =>
    apiRequest<Account[]>(`/api/admin/users?limit=${ADMIN_USERS_PAGE_SIZE}&offset=${(page - 1) * ADMIN_USERS_PAGE_SIZE}`),
  changeSubscription: (userId: number, change: SubscriptionChange) =>
    apiRequest<Subscription>(`/api/admin/users/${userId}/subscription`, { method: 'POST', body: change }),
}

export const adminBillingKeys = {
  payments: ['admin', 'payments'] as const,
  paymentsPage: (filters: AdminPaymentFilters) => ['admin', 'payments', filters] as const,
  users: (page: number) => ['admin', 'users', page] as const,
}
