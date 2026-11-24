import { errorMessage } from '../../api/errors'
import { useStartCheckout } from '../../billing/mutations'
import type { PlanCode } from '../../types/playback'
import FormAlert from '../FormAlert'
import { buttonPrimary } from '../ui'

interface CheckoutButtonProps {
  planCode: PlanCode
  label: string
}

export default function CheckoutButton({ planCode, label }: CheckoutButtonProps) {
  const checkout = useStartCheckout()

  return (
    <div className="space-y-3">
      {checkout.isError && <FormAlert>{errorMessage(checkout.error)}</FormAlert>}
      <button
        type="button"
        className={`${buttonPrimary} w-full`}
        disabled={checkout.isPending}
        onClick={() => checkout.mutate(planCode)}
      >
        {checkout.isPending ? 'Створюємо платіж…' : label}
      </button>
    </div>
  )
}
