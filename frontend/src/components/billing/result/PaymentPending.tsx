import { errorMessage } from '../../../api/errors'
import { useSubmitPaymentResult } from '../../../billing/mutations'
import type { Payment } from '../../../types/billing'
import FormAlert from '../../FormAlert'
import StateMessage from '../../StateMessage'
import { buttonDanger, buttonPrimary } from '../../ui'

export default function PaymentPending({ payment }: { payment: Payment }) {
  const submit = useSubmitPaymentResult(payment.id)

  return (
    <div className="space-y-4">
      {submit.isError && <FormAlert>{errorMessage(submit.error)}</FormAlert>}
      <StateMessage
        title="Оплата очікує підтвердження"
        text="Банк ще перевіряє платіж. Преміум активується одразу після підтвердження, а поки діє ваш поточний план. У тестовому режимі відповідь банку можна задати тут."
        action={
          <div className="flex flex-wrap justify-center gap-3">
            <button
              type="button"
              className={buttonPrimary}
              disabled={submit.isPending}
              onClick={() => submit.mutate('success')}
            >
              Підтвердити оплату
            </button>
            <button
              type="button"
              className={buttonDanger}
              disabled={submit.isPending}
              onClick={() => submit.mutate('failed')}
            >
              Відхилити
            </button>
          </div>
        }
      />
    </div>
  )
}
