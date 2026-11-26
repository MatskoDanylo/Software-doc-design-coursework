import type { UseQueryResult } from '@tanstack/react-query'
import { errorMessage } from '../../api/errors'
import { useAdminPayments, usePaymentFilters } from '../../admin/billing'
import AdminPaymentRow from '../../components/admin/billing/AdminPaymentRow'
import PaymentStatusFilter from '../../components/admin/billing/PaymentStatusFilter'
import Pagination from '../../components/Pagination'
import { TableSkeleton } from '../../components/Skeletons'
import StateMessage from '../../components/StateMessage'
import type { AdminPaymentPage } from '../../types/adminBilling'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

const HEADERS = ['№', 'Створено', 'Користувач', 'Тариф', 'Сума', 'Статус', 'Дії']

interface PaymentsTableProps {
  query: UseQueryResult<AdminPaymentPage>
  onPageChange: (page: number) => void
}

function PaymentsTable({ query, onPageChange }: PaymentsTableProps) {
  if (query.isPending) return <TableSkeleton columns={6} />
  if (query.isError) return <StateMessage tone="error" title="Не вдалося завантажити платежі" text={errorMessage(query.error)} />
  if (query.data.items.length === 0) return <StateMessage title="Платежів з таким статусом немає" />

  const { items, total, page, page_size } = query.data
  return (
    <div className="space-y-6">
      <div className="overflow-x-auto">
        <table className={`w-full text-left text-sm ${query.isPlaceholderData ? 'opacity-60' : ''}`}>
          <thead className="border-b border-line text-xs text-muted uppercase">
            <tr>
              {HEADERS.map((header) => (
                <th key={header} scope="col" className="py-2 pr-3 font-medium">
                  <span className={header === 'Дії' ? 'sr-only' : undefined}>{header}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {items.map((payment) => (
              <AdminPaymentRow key={payment.id} payment={payment} />
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} totalPages={Math.ceil(total / page_size)} onChange={onPageChange} />
    </div>
  )
}

export default function AdminPaymentsPage() {
  useDocumentTitle('Платежі — Адмінка')
  const { filters, update } = usePaymentFilters()
  const query = useAdminPayments(filters)

  return (
    <section className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Платежі</h1>
        {query.data && <p className="mt-1 text-sm text-muted">Знайдено: {query.data.total}</p>}
      </div>
      <div className="max-w-xs">
        <PaymentStatusFilter value={filters.status} onChange={(status) => update({ status })} />
      </div>
      <PaymentsTable query={query} onPageChange={(page) => update({ page })} />
    </section>
  )
}
