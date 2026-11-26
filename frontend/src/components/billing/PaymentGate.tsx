import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { errorMessage } from '../../api/errors'
import { parseId } from '../../billing/paths'
import { usePayment } from '../../billing/queries'
import type { Payment } from '../../types/billing'
import PageLoader from '../PageLoader'
import StateMessage from '../StateMessage'
import { buttonOutline } from '../ui'

interface PaymentGateProps {
  children: (payment: Payment) => ReactNode
}

export default function PaymentGate({ children }: PaymentGateProps) {
  const paymentId = parseId(useParams().paymentId)
  const query = usePayment(paymentId ?? 0)
  const pricingLink = (
    <Link to="/pricing" className={buttonOutline}>
      До тарифів
    </Link>
  )

  if (paymentId !== null && query.isPending) return <PageLoader />
  if (query.isError) {
    return <StateMessage tone="error" title="Не вдалося завантажити платіж" text={errorMessage(query.error)} action={pricingLink} />
  }
  if (paymentId !== null && query.data === null && query.isFetching) return <PageLoader />
  if (paymentId === null || !query.data) {
    return <StateMessage title="Платіж не знайдено" text="Можливо, посилання застаріло" action={pricingLink} />
  }
  return children(query.data)
}
