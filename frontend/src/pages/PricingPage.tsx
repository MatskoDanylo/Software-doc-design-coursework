import { errorMessage } from '../api/errors'
import { useAuth } from '../auth/useAuth'
import { usePlans } from '../billing/queries'
import PlanAction from '../components/billing/PlanAction'
import PlanCard from '../components/billing/PlanCard'
import PageLoader from '../components/PageLoader'
import StateMessage from '../components/StateMessage'

export default function PricingPage() {
  const { user, status } = useAuth()
  const plans = usePlans()

  if (plans.isPending || status === 'loading') return <PageLoader />
  if (plans.isError) {
    return <StateMessage tone="error" title="Не вдалося завантажити тарифи" text={errorMessage(plans.error)} />
  }

  const currentCode = user?.subscription.plan_code ?? null
  return (
    <section className="space-y-8">
      <header>
        <h1 className="font-display text-3xl font-semibold">Тарифи</h1>
        <p className="mt-2 text-muted">Free з рекламою або Premium без реклами у вищій якості</p>
      </header>
      <div className="grid gap-6 md:grid-cols-2">
        {plans.data.map((plan) => (
          <PlanCard
            key={plan.code}
            plan={plan}
            current={plan.code === currentCode}
            action={<PlanAction plan={plan} current={plan.code === currentCode} guest={user === null} />}
          />
        ))}
      </div>
    </section>
  )
}
