import { formatMoney } from '../../../billing/format'
import { PLAN_LABELS } from '../../../billing/planLabels'
import { formatDateTime } from '../../../format/datetime'
import type { AdminPayment } from '../../../types/adminBilling'
import PaymentStatusBadge from '../../billing/PaymentStatusBadge'
import ResolveActions from './ResolveActions'

export default function AdminPaymentRow({ payment }: { payment: AdminPayment }) {
  return (
    <tr className="align-middle">
      <td className="py-2 pr-3 text-muted">№{payment.id}</td>
      <td className="py-2 pr-3 whitespace-nowrap text-muted">{formatDateTime(payment.created_at)}</td>
      <td className="max-w-56 truncate py-2 pr-3">{payment.user_email}</td>
      <td className="py-2 pr-3">{PLAN_LABELS[payment.plan_code]}</td>
      <td className="py-2 pr-3 whitespace-nowrap">{formatMoney(payment.amount, payment.currency)}</td>
      <td className="py-2 pr-3">
        <PaymentStatusBadge status={payment.status} />
      </td>
      <td className="py-2">{payment.status === 'pending' && <ResolveActions paymentId={payment.id} />}</td>
    </tr>
  )
}
