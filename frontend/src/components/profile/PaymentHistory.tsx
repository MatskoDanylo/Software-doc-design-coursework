import { errorMessage } from '../../api/errors'
import { usePayments } from '../../billing/queries'
import { card } from '../ui'
import PaymentRow from './PaymentRow'

const HEADERS = ['Дата', 'Тариф', 'Сума', 'Статус', 'Дія']

function HistoryBody() {
  const payments = usePayments()

  if (payments.isPending) return <p className="text-sm text-muted">Завантаження…</p>
  if (payments.isError) return <p className="text-sm text-danger">{errorMessage(payments.error)}</p>
  if (payments.data.length === 0) return <p className="text-sm text-muted">Платежів ще не було</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-line text-xs text-muted uppercase">
          <tr>
            {HEADERS.map((header) => (
              <th key={header} scope="col" className="py-2 pr-3 font-medium">
                <span className={header === 'Дія' ? 'sr-only' : undefined}>{header}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {payments.data.map((payment) => (
            <PaymentRow key={payment.id} payment={payment} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function PaymentHistory() {
  return (
    <section aria-labelledby="payments-heading" className={card}>
      <h2 id="payments-heading" className="font-display text-xl font-semibold">
        Історія платежів
      </h2>
      <div className="mt-4">
        <HistoryBody />
      </div>
    </section>
  )
}
