import type { PlanCode } from './playback'

export type PaymentStatus = 'created' | 'pending' | 'success' | 'failed'
export type PaymentOutcome = 'success' | 'pending' | 'failed'

export interface Plan {
  code: PlanCode
  name: string
  price: string
  currency: string
  duration_days: number | null
  ads_enabled: boolean
  max_height: number
  description: string
  purchasable: boolean
}

export interface CheckoutResult {
  payment_id: number
  amount: string
  currency: string
  status: PaymentStatus
  plan: Plan
}

export interface Payment {
  id: number
  plan_code: PlanCode
  amount: string
  currency: string
  status: PaymentStatus
  created_at: string
  paid_at: string | null
}
