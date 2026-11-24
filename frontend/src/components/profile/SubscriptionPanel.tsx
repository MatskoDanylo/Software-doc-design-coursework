import { Link } from 'react-router-dom'
import { errorMessage } from '../../api/errors'
import { useCancelSubscription } from '../../billing/mutations'
import { planFeatures } from '../../billing/planFeatures'
import { PLAN_LABELS } from '../../billing/planLabels'
import { usePlan } from '../../billing/queries'
import { formatDate } from '../../format/datetime'
import { sentence } from '../../format/text'
import type { Subscription } from '../../types/user'
import ConfirmButton from '../admin/ConfirmButton'
import FormAlert from '../FormAlert'
import { buttonOutline, buttonPrimary, card } from '../ui'

function statusText({ plan_code, expires_at, cancelled }: Subscription): string {
  if (plan_code === 'free' || expires_at === null) return 'Безкоштовний план без обмеження в часі.'
  const until = formatDate(expires_at)
  return sentence(cancelled ? `Підписку скасовано. Доступ зберігається до ${until}` : `Діє до ${until}`)
}

function SubscriptionActions({ subscription }: { subscription: Subscription }) {
  const cancel = useCancelSubscription()

  if (subscription.plan_code === 'free' || subscription.cancelled) {
    return (
      <Link to="/pricing" className={buttonPrimary}>
        {subscription.cancelled ? 'Відновити Premium' : 'Оформити Premium'}
      </Link>
    )
  }
  const until = subscription.expires_at ? formatDate(subscription.expires_at) : ''
  return (
    <div className="space-y-3">
      {cancel.isError && <FormAlert>{errorMessage(cancel.error)}</FormAlert>}
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/pricing" className={buttonOutline}>
          Продовжити
        </Link>
        <ConfirmButton
          label="Скасувати підписку"
          question={sentence(`Скасувати Premium? Доступ збережеться до ${until}`)}
          confirmLabel="Так, скасувати"
          pendingLabel="Скасування…"
          dismissLabel="Ні"
          pending={cancel.isPending}
          onConfirm={() => cancel.mutate()}
        />
      </div>
    </div>
  )
}

export default function SubscriptionPanel({ subscription }: { subscription: Subscription }) {
  const plan = usePlan(subscription.plan_code)

  return (
    <section aria-labelledby="subscription-heading" className={card}>
      <h2 id="subscription-heading" className="font-display text-xl font-semibold">
        Підписка
      </h2>
      <p className="mt-4 font-display text-2xl font-semibold text-gold">
        {plan?.name ?? PLAN_LABELS[subscription.plan_code]}
      </p>
      <p className="mt-1 text-sm text-zinc-300">{statusText(subscription)}</p>
      {plan && <p className="mt-1 text-sm text-muted">{planFeatures(plan).join(' · ')}</p>}
      <div className="mt-6">
        <SubscriptionActions subscription={subscription} />
      </div>
    </section>
  )
}
