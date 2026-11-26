import { Navigate } from 'react-router-dom'
import { checkoutPath } from '../billing/paths'
import PaymentGate from '../components/billing/PaymentGate'
import PaymentFailed from '../components/billing/result/PaymentFailed'
import PaymentPending from '../components/billing/result/PaymentPending'
import PaymentSucceeded from '../components/billing/result/PaymentSucceeded'
import type { Payment } from '../types/billing'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

function PaymentResult({ payment }: { payment: Payment }) {
  switch (payment.status) {
    case 'created':
      return <Navigate to={checkoutPath(payment.id)} replace />
    case 'pending':
      return <PaymentPending payment={payment} />
    case 'success':
      return <PaymentSucceeded payment={payment} />
    case 'failed':
      return <PaymentFailed payment={payment} />
  }
}

export default function PaymentResultPage() {
  useDocumentTitle('Результат оплати')
  return (
    <section className="mx-auto max-w-xl space-y-6">
      <h1 className="font-display text-3xl font-semibold">Результат оплати</h1>
      <PaymentGate>{(payment) => <PaymentResult payment={payment} />}</PaymentGate>
    </section>
  )
}
