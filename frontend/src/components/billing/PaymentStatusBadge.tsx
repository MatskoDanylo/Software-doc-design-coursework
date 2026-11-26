import { PAYMENT_STATUS } from '../../billing/statuses'
import type { PaymentStatus } from '../../types/billing'

export default function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const { label, className } = PAYMENT_STATUS[status]
  return <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${className}`}>{label}</span>
}
