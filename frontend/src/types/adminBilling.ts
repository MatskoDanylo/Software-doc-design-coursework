import type { Payment, PaymentStatus } from './billing'

export interface AdminPayment extends Payment {
  user_id: number
  user_email: string
}

export interface AdminPaymentPage {
  items: AdminPayment[]
  total: number
  page: number
  page_size: number
}

export interface AdminPaymentFilters {
  status: PaymentStatus | null
  page: number
}

export type ResolveOutcome = 'success' | 'failed'

export interface SubscriptionChange {
  action: 'grant' | 'revoke'
  days?: number
}
