import { useQuery } from '@tanstack/react-query'
import { billingApi, billingKeys } from '../api/billing'
import type { Payment, Plan } from '../types/billing'
import type { PlanCode } from '../types/playback'

const PLANS_STALE_MS = 5 * 60 * 1000

export function usePlans() {
  return useQuery({ queryKey: billingKeys.plans, queryFn: billingApi.plans, staleTime: PLANS_STALE_MS })
}

export function usePlan(code: PlanCode): Plan | undefined {
  return usePlans().data?.find((plan) => plan.code === code)
}

export function usePayments() {
  return useQuery({ queryKey: billingKeys.payments, queryFn: billingApi.payments })
}

export function usePayment(paymentId: number) {
  return useQuery({
    queryKey: billingKeys.payments,
    queryFn: billingApi.payments,
    select: (payments: Payment[]) => payments.find((payment) => payment.id === paymentId) ?? null,
  })
}
