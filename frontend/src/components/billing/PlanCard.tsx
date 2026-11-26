import type { ReactNode } from 'react'
import { formatMoney } from '../../billing/format'
import { planFeatures } from '../../billing/planFeatures'
import type { Plan } from '../../types/billing'

interface PlanCardProps {
  plan: Plan
  current: boolean
  action?: ReactNode
}

export default function PlanCard({ plan, current, action }: PlanCardProps) {
  const headingId = `plan-${plan.code}`

  return (
    <article
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border bg-surface p-6 sm:p-8 ${current ? 'border-gold' : 'border-line'}`}
    >
      <div className="flex items-center justify-between gap-3">
        <h2 id={headingId} className="font-display text-2xl font-semibold">
          {plan.name}
        </h2>
        {current && (
          <span className="rounded-full border border-gold/50 bg-gold/10 px-3 py-0.5 text-xs font-medium text-gold">
            Ваш план
          </span>
        )}
      </div>
      <p className="mt-4 font-display text-3xl font-semibold">
        {formatMoney(plan.price, plan.currency)}
        {plan.duration_days !== null && <span className="text-base text-muted"> / {plan.duration_days} днів</span>}
      </p>
      <ul className="mt-6 space-y-2 text-sm text-zinc-300">
        {planFeatures(plan).map((feature) => (
          <li key={feature} className="flex gap-2">
            <span aria-hidden="true" className="text-gold">
              ✓
            </span>
            {feature}
          </li>
        ))}
      </ul>
      {action && <div className="mt-auto pt-8">{action}</div>}
    </article>
  )
}
