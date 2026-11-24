import type { Payment, PaymentOutcome, Plan } from '../types/billing'

export const freePlan: Plan = {
  code: 'free',
  name: 'Free',
  price: '0.00',
  currency: 'UAH',
  duration_days: null,
  ads_enabled: true,
  max_height: 720,
  description: 'Безкоштовно назавжди. Реклама перед відео, якість до 720p.',
  purchasable: false,
}

export const premiumPlan: Plan = {
  code: 'premium',
  name: 'Premium',
  price: '99.00',
  currency: 'UAH',
  duration_days: 30,
  ads_enabled: false,
  max_height: 1080,
  description: '99.00 грн за 30 днів. Без реклами, якість до 1080p.',
  purchasable: true,
}

export const plans: Plan[] = [freePlan, premiumPlan]

export function makePayment(patch: Partial<Payment> = {}): Payment {
  return {
    id: 7,
    plan_code: 'premium',
    amount: '99.00',
    currency: 'UAH',
    status: 'created',
    created_at: '2026-11-25T10:00:00Z',
    paid_at: null,
    ...patch,
  }
}

const OUTCOMES: readonly PaymentOutcome[] = ['success', 'pending', 'failed']

export function outcomeFrom(init?: RequestInit): PaymentOutcome | null {
  const body: unknown = JSON.parse(String(init?.body ?? 'null'))
  if (typeof body !== 'object' || body === null || !('outcome' in body)) return null
  return OUTCOMES.find((outcome) => outcome === body.outcome) ?? null
}

export function settledPayment(payment: Payment, outcome: PaymentOutcome): Payment {
  return { ...payment, status: outcome, paid_at: outcome === 'success' ? '2026-11-25T10:05:00Z' : null }
}
