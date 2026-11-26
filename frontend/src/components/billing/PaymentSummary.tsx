import { formatMoney } from '../../billing/format'
import { PLAN_LABELS } from '../../billing/planLabels'
import { usePlan } from '../../billing/queries'
import type { Payment } from '../../types/billing'

export default function PaymentSummary({ payment }: { payment: Payment }) {
  const plan = usePlan(payment.plan_code)

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
      <dt className="text-muted">Тариф</dt>
      <dd className="font-medium">
        {plan?.name ?? PLAN_LABELS[payment.plan_code]}
        {plan && plan.duration_days !== null && <span className="text-muted"> · {plan.duration_days} днів</span>}
      </dd>
      <dt className="text-muted">Сума</dt>
      <dd className="font-display text-2xl font-semibold">{formatMoney(payment.amount, payment.currency)}</dd>
      <dt className="text-muted">Платіж</dt>
      <dd>№{payment.id}</dd>
    </dl>
  )
}
