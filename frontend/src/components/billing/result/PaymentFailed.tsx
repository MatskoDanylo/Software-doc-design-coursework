import { Link } from 'react-router-dom'
import { errorMessage } from '../../../api/errors'
import { useStartCheckout } from '../../../billing/mutations'
import type { Payment } from '../../../types/billing'
import FormAlert from '../../FormAlert'
import StateMessage from '../../StateMessage'
import { buttonOutline, buttonPrimary } from '../../ui'

export default function PaymentFailed({ payment }: { payment: Payment }) {
  const checkout = useStartCheckout()

  return (
    <div className="space-y-4">
      {checkout.isError && <FormAlert>{errorMessage(checkout.error)}</FormAlert>}
      <StateMessage
        tone="error"
        title="Оплату відхилено"
        text="Гроші не списано, підписка не змінилась."
        action={
          <div className="flex flex-wrap justify-center gap-3">
            <button
              type="button"
              className={buttonPrimary}
              disabled={checkout.isPending}
              onClick={() => checkout.mutate(payment.plan_code)}
            >
              {checkout.isPending ? 'Створюємо платіж…' : 'Спробувати знову'}
            </button>
            <Link to="/pricing" className={buttonOutline}>
              До тарифів
            </Link>
          </div>
        }
      />
    </div>
  )
}
