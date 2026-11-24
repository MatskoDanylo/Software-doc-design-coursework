import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { billingApi, billingKeys } from '../api/billing'
import type { Payment, PaymentOutcome } from '../types/billing'
import type { PlanCode } from '../types/playback'
import { checkoutPath } from './paths'
import { usePlanRefresh } from './usePlanRefresh'

export function useStartCheckout() {
  const client = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (planCode: PlanCode) => billingApi.checkout(planCode),
    onSuccess: async (result) => {
      await client.invalidateQueries({ queryKey: billingKeys.payments })
      navigate(checkoutPath(result.payment_id))
    },
  })
}

export function useSubmitPaymentResult(paymentId: number) {
  const client = useQueryClient()
  const refreshPlan = usePlanRefresh()

  return useMutation({
    mutationFn: (outcome: PaymentOutcome) => billingApi.submitMockResult(paymentId, outcome),
    onSuccess: async (payment) => {
      client.setQueryData<Payment[]>(billingKeys.payments, (payments) =>
        payments?.map((item) => (item.id === payment.id ? payment : item)),
      )
      if (payment.status === 'success') await refreshPlan()
    },
    onSettled: () => client.invalidateQueries({ queryKey: billingKeys.payments }),
  })
}
