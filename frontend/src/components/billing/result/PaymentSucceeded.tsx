import { Link } from 'react-router-dom'
import { useAuth } from '../../../auth/useAuth'
import { formatDate } from '../../../billing/format'
import { usePlan } from '../../../billing/queries'
import type { Payment } from '../../../types/billing'
import StateMessage from '../../StateMessage'
import { buttonOutline, buttonPrimary } from '../../ui'

export default function PaymentSucceeded({ payment }: { payment: Payment }) {
  const { user } = useAuth()
  const plan = usePlan(payment.plan_code)
  const subscription = user?.subscription.plan_code === payment.plan_code ? user.subscription : null
  const name = plan?.name ?? payment.plan_code
  const until = subscription?.expires_at ? ` до ${formatDate(subscription.expires_at)}` : ''
  const perks = plan ? ` Відео без реклами, якість до ${plan.max_height}p.` : ''

  return (
    <StateMessage
      title="Оплату прийнято"
      text={`План ${name} активний${until}.${perks}`}
      action={
        <div className="flex flex-wrap justify-center gap-3">
          <Link to="/catalog" className={buttonPrimary}>
            ▶ Дивитись
          </Link>
          <Link to="/profile" className={buttonOutline}>
            До профілю
          </Link>
        </div>
      }
    />
  )
}
