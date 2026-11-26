import { useResolvePayment } from '../../../admin/billing'
import { buttonDanger, buttonPrimary, buttonSmall } from '../../ui'

export default function ResolveActions({ paymentId }: { paymentId: number }) {
  const resolve = useResolvePayment(paymentId)

  return (
    <div className="flex flex-wrap justify-end gap-2">
      <button
        type="button"
        className={`${buttonPrimary} ${buttonSmall}`}
        disabled={resolve.isPending}
        onClick={() => resolve.mutate('success')}
      >
        Підтвердити
      </button>
      <button
        type="button"
        className={`${buttonDanger} ${buttonSmall}`}
        disabled={resolve.isPending}
        onClick={() => resolve.mutate('failed')}
      >
        Відхилити
      </button>
    </div>
  )
}
