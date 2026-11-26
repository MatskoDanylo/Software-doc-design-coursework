import { Link } from 'react-router-dom'
import type { PlanCode } from '../../types/playback'
import { textLink } from '../ui'

const BADGE: Record<PlanCode, { label: string; className: string }> = {
  free: { label: 'Безкоштовний', className: 'border-line text-zinc-300' },
  premium: { label: 'Преміум', className: 'border-gold/50 bg-gold/10 text-gold' },
}

export default function PlanBadge({ plan }: { plan: PlanCode | null }) {
  if (plan === null) return null
  const badge = BADGE[plan]

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      <span className={`rounded-full border px-3 py-0.5 text-xs font-medium ${badge.className}`}>План: {badge.label}</span>
      {plan === 'free' && (
        <Link to="/pricing" className={textLink}>
          Преміум: до 1080p без реклами
        </Link>
      )}
    </div>
  )
}
