import type { PaymentStatus } from '../types/billing'

export const PAYMENT_STATUS: Record<PaymentStatus, { label: string; className: string }> = {
  created: { label: 'Не оплачено', className: 'border-line text-zinc-300' },
  pending: { label: 'Очікує підтвердження', className: 'border-amber-400/50 bg-amber-400/10 text-amber-200' },
  success: { label: 'Оплачено', className: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' },
  failed: { label: 'Відхилено', className: 'border-danger/40 bg-danger/10 text-danger' },
}

export function isPaymentStatus(value: string | null): value is PaymentStatus {
  return value !== null && Object.hasOwn(PAYMENT_STATUS, value)
}
