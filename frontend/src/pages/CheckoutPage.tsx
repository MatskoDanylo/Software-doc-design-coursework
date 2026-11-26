import { Navigate } from 'react-router-dom'
import { paymentResultPath } from '../billing/paths'
import CheckoutForm from '../components/billing/CheckoutForm'
import PaymentGate from '../components/billing/PaymentGate'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export default function CheckoutPage() {
  useDocumentTitle('Оплата')
  return (
    <section className="mx-auto max-w-xl space-y-6">
      <h1 className="font-display text-3xl font-semibold">Оплата підписки</h1>
      <PaymentGate>
        {(payment) =>
          payment.status === 'created' ? (
            <CheckoutForm payment={payment} />
          ) : (
            <Navigate to={paymentResultPath(payment.id)} replace />
          )
        }
      </PaymentGate>
    </section>
  )
}
