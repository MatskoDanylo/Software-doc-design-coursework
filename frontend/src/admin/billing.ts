import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { adminBillingApi, adminBillingKeys } from '../api/adminBilling'
import { useAuth } from '../auth/useAuth'
import { isPaymentStatus } from '../billing/statuses'
import { usePlanRefresh } from '../billing/usePlanRefresh'
import type { AdminPaymentFilters, ResolveOutcome, SubscriptionChange } from '../types/adminBilling'

export function parsePage(value: string | null): number {
  const page = Number(value)
  return Number.isInteger(page) && page > 0 ? page : 1
}

export function usePaymentFilters() {
  const [params, setParams] = useSearchParams()
  const status = params.get('status')
  const filters = useMemo<AdminPaymentFilters>(
    () => ({ status: isPaymentStatus(status) ? status : null, page: parsePage(params.get('page')) }),
    [params, status],
  )

  const update = useCallback(
    (patch: Partial<AdminPaymentFilters>) =>
      setParams(() => {
        const next = { ...filters, page: 1, ...patch }
        const query = new URLSearchParams()
        if (next.status) query.set('status', next.status)
        if (next.page > 1) query.set('page', String(next.page))
        return query
      }),
    [filters, setParams],
  )

  return { filters, update }
}

export function useAdminPayments(filters: AdminPaymentFilters) {
  return useQuery({
    queryKey: adminBillingKeys.paymentsPage(filters),
    queryFn: () => adminBillingApi.payments(filters),
    placeholderData: keepPreviousData,
  })
}

function useOwnPlanRefresh() {
  const { user } = useAuth()
  const refreshPlan = usePlanRefresh()
  return useCallback((userId: number) => (user?.id === userId ? refreshPlan() : undefined), [user, refreshPlan])
}

export function useResolvePayment(paymentId: number) {
  const client = useQueryClient()
  const refreshOwnPlan = useOwnPlanRefresh()
  return useMutation({
    mutationFn: (outcome: ResolveOutcome) => adminBillingApi.resolve(paymentId, outcome),
    onSuccess: (payment) => refreshOwnPlan(payment.user_id),
    onSettled: () => client.invalidateQueries({ queryKey: adminBillingKeys.payments }),
  })
}

export function useAdminUsers(page: number) {
  return useQuery({
    queryKey: adminBillingKeys.users(page),
    queryFn: () => adminBillingApi.users(page),
    placeholderData: keepPreviousData,
  })
}

export function useChangeSubscription(userId: number) {
  const refreshOwnPlan = useOwnPlanRefresh()
  return useMutation({
    mutationFn: (change: SubscriptionChange) => adminBillingApi.changeSubscription(userId, change),
    onSuccess: () => refreshOwnPlan(userId),
  })
}
