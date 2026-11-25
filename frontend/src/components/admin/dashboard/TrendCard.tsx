import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../../../api/errors'
import ChartCard from '../../charts/ChartCard'
import { textLink } from '../../ui'

interface TrendCardProps {
  title: string
  to: string
  state: { isPending: boolean; isError: boolean; error: unknown }
  children: ReactNode
}

const placeholderClass = 'flex h-[180px] items-center justify-center rounded-lg'

export default function TrendCard({ title, to, state, children }: TrendCardProps) {
  const action = (
    <Link to={to} className={`${textLink} text-xs`}>
      Детальніше →
    </Link>
  )

  return (
    <ChartCard title={title} action={action}>
      {state.isPending && (
        <div role="status" className={`${placeholderClass} animate-pulse bg-surface-raised`}>
          <span className="sr-only">Завантаження…</span>
        </div>
      )}
      {state.isError && <p className={`${placeholderClass} text-sm text-danger`}>{errorMessage(state.error)}</p>}
      {!state.isPending && !state.isError && children}
    </ChartCard>
  )
}
