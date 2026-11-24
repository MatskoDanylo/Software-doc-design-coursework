import type { CheckoutResult, Payment, PaymentOutcome, Plan } from '../types/billing'
import type { PlanCode } from '../types/playback'
import { apiRequest } from './client'

export const billingApi = {
  plans: () => apiRequest<Plan[]>('/api/plans', { auth: false }),
  checkout: (planCode: PlanCode) =>
    apiRequest<CheckoutResult>('/api/billing/checkout', { method: 'POST', body: { plan_code: planCode } }),
  payments: () => apiRequest<Payment[]>('/api/billing/payments'),
  submitMockResult: (paymentId: number, outcome: PaymentOutcome) =>
    apiRequest<Payment>(`/api/billing/payments/${paymentId}/mock-result`, { method: 'POST', body: { outcome } }),
}

export const billingKeys = {
  plans: ['plans'] as const,
  payments: ['billing', 'payments'] as const,
}
