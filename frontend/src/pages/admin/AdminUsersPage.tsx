import { useSearchParams } from 'react-router-dom'
import { ADMIN_USERS_PAGE_SIZE } from '../../api/adminBilling'
import { errorMessage } from '../../api/errors'
import { parsePage, useAdminUsers } from '../../admin/billing'
import AdminUserRow from '../../components/admin/users/AdminUserRow'
import { TableSkeleton } from '../../components/Skeletons'
import StateMessage from '../../components/StateMessage'
import { buttonGhost, buttonSmall } from '../../components/ui'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

const HEADERS = ['Користувач', 'Роль', 'Реєстрація', 'Підписка']

function Pager({ page, hasNext, onChange }: { page: number; hasNext: boolean; onChange: (page: number) => void }) {
  if (page === 1 && !hasNext) return null
  return (
    <nav aria-label="Сторінки" className="flex items-center justify-center gap-3 text-sm">
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Назад
      </button>
      <span className="text-muted">Сторінка {page}</span>
      <button type="button" className={`${buttonGhost} ${buttonSmall}`} disabled={!hasNext} onClick={() => onChange(page + 1)}>
        Далі →
      </button>
    </nav>
  )
}

export default function AdminUsersPage() {
  useDocumentTitle('Користувачі — Адмінка')
  const [params, setParams] = useSearchParams()
  const page = parsePage(params.get('page'))
  const query = useAdminUsers(page)
  const changePage = (next: number) => setParams(next > 1 ? { page: String(next) } : {})

  return (
    <section className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Користувачі</h1>
        <p className="mt-1 text-sm text-muted">
          Видача Преміуму без оплати. Порожнє поле днів означає тривалість тарифу.
        </p>
      </div>
      {query.isPending && <TableSkeleton columns={4} />}
      {query.isError && <StateMessage tone="error" title="Не вдалося завантажити користувачів" text={errorMessage(query.error)} />}
      {query.data?.length === 0 && (
        <StateMessage title="Користувачів не знайдено" text={page > 1 ? 'На цій сторінці нікого немає' : undefined} />
      )}
      {query.data && query.data.length > 0 && (
        <div className="space-y-6">
          <div className="overflow-x-auto">
            <table className={`w-full text-left text-sm ${query.isPlaceholderData ? 'opacity-60' : ''}`}>
              <thead className="border-b border-line text-xs text-muted uppercase">
                <tr>
                  {HEADERS.map((header) => (
                    <th key={header} scope="col" className="py-2 pr-3 font-medium">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {query.data.map((user) => (
                  <AdminUserRow key={user.id} user={user} />
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} hasNext={query.data.length === ADMIN_USERS_PAGE_SIZE} onChange={changePage} />
        </div>
      )}
    </section>
  )
}
