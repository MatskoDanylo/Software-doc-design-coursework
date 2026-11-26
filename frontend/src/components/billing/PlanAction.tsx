import { Link } from 'react-router-dom'
import type { RedirectState } from '../../routes/redirect'
import type { Plan } from '../../types/billing'
import { buttonPrimary } from '../ui'
import CheckoutButton from './CheckoutButton'

interface PlanActionProps {
  plan: Plan
  current: boolean
  guest: boolean
}

const fromPricing: RedirectState = { from: '/pricing' }

export default function PlanAction({ plan, current, guest }: PlanActionProps) {
  if (!plan.purchasable) return null
  const label = current ? `Продовжити ${plan.name}` : `Оформити ${plan.name}`

  if (guest) {
    return (
      <Link to="/login" state={fromPricing} className={`${buttonPrimary} w-full`}>
        {label}
      </Link>
    )
  }
  return <CheckoutButton planCode={plan.code} label={label} />
}
