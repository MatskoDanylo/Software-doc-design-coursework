import { Link } from 'react-router-dom'
import { formatDate, formatMoney } from '../../billing/format'
import { checkoutPath, paymentResultPath } from '../../billing/paths'
import { PLAN_LABELS } from '../../billing/planLabels'
import type { Payment } from '../../types/billing'
import PaymentStatusBadge from '../billing/PaymentStatusBadge'
import { textLink } from '../ui'

function PaymentAction({ payment }: { payment: Payment }) {
  if (payment.status === 'created') {
    return (
      <Link to={checkoutPath(payment.id)} className={textLink}>
        Оплатити
      </Link>
    )
  }
  if (payment.status === 'pending') {
    return (
      <Link to={paymentResultPath(payment.id)} className={textLink}>
        Деталі
      </Link>
    )
  }
  return null
}

export default function PaymentRow({ payment }: { payment: Payment }) {
  return (
    <tr>
      <td className="py-2 pr-3 whitespace-nowrap">{formatDate(payment.created_at)}</td>
      <td className="py-2 pr-3">{PLAN_LABELS[payment.plan_code]}</td>
      <td className="py-2 pr-3 whitespace-nowrap">{formatMoney(payment.amount, payment.currency)}</td>
      <td className="py-2 pr-3">
        <PaymentStatusBadge status={payment.status} />
      </td>
      <td className="py-2 text-right">
        <PaymentAction payment={payment} />
      </td>
    </tr>
  )
}
