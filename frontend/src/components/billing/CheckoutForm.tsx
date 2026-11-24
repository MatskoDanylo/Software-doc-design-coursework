import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../../api/errors'
import { useSubmitPaymentResult } from '../../billing/mutations'
import { paymentResultPath } from '../../billing/paths'
import type { Payment, PaymentOutcome } from '../../types/billing'
import FormAlert from '../FormAlert'
import { buttonPrimary, card } from '../ui'
import OutcomePicker from './OutcomePicker'
import PaymentSummary from './PaymentSummary'
import TestPaymentBanner from './TestPaymentBanner'

export default function CheckoutForm({ payment }: { payment: Payment }) {
  const [outcome, setOutcome] = useState<PaymentOutcome>('success')
  const submit = useSubmitPaymentResult(payment.id)
  const navigate = useNavigate()

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submit.mutate(outcome, { onSuccess: () => navigate(paymentResultPath(payment.id)) })
  }

  return (
    <form onSubmit={handleSubmit} className={`${card} space-y-6`}>
      <TestPaymentBanner />
      <PaymentSummary payment={payment} />
      <OutcomePicker value={outcome} onChange={setOutcome} />
      {submit.isError && <FormAlert>{errorMessage(submit.error)}</FormAlert>}
      <button type="submit" disabled={submit.isPending} className={`${buttonPrimary} w-full`}>
        {submit.isPending ? 'Обробка…' : 'Оплатити'}
      </button>
    </form>
  )
}
