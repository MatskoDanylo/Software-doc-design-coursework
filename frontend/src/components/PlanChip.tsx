import { Link } from 'react-router-dom'
import { PLAN_LABELS } from '../billing/planLabels'
import type { PlanCode } from '../types/playback'

const CHIP_CLASS: Record<PlanCode, string> = {
  free: 'border-line text-zinc-300 hover:border-gold hover:text-gold',
  premium: 'border-gold/50 bg-gold/10 text-gold',
}

export default function PlanChip({ plan }: { plan: PlanCode }) {
  return (
    <Link
      to="/pricing"
      aria-label={`Ваш план: ${PLAN_LABELS[plan]}`}
      className={`rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ${CHIP_CLASS[plan]}`}
    >
      {PLAN_LABELS[plan]}
    </Link>
  )
}
