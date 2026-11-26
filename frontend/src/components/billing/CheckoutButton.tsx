import { useStartCheckout } from '../../billing/mutations'
import type { PlanCode } from '../../types/playback'
import { buttonPrimary } from '../ui'

interface CheckoutButtonProps {
  planCode: PlanCode
  label: string
}

export default function CheckoutButton({ planCode, label }: CheckoutButtonProps) {
  const checkout = useStartCheckout()

  return (
    <button
      type="button"
      className={`${buttonPrimary} w-full`}
      disabled={checkout.isPending}
      onClick={() => checkout.mutate(planCode)}
    >
      {checkout.isPending ? 'Створюємо платіж…' : label}
    </button>
  )
}
