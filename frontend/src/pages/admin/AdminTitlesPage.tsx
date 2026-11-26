import { keepPreviousData, useQuery, type UseQueryResult } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { catalogApi, catalogKeys } from '../../api/catalog'
import { errorMessage } from '../../api/errors'
import { useCatalogFilters } from '../../catalog/useCatalogFilters'
import AdminTitleRow from '../../components/admin/AdminTitleRow'
import SearchInput from '../../components/catalog/SearchInput'
import Pagination from '../../components/Pagination'
import { TableSkeleton } from '../../components/Skeletons'
import StateMessage from '../../components/StateMessage'
import { buttonPrimary } from '../../components/ui'
import type { TitlePage, TitleSearchParams } from '../../types/catalog'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

const ADMIN_PAGE_SIZE = 20
const HEADERS = ['Постер', 'Назва', 'Тип', 'Рік', 'Країна', 'Рейтинг', 'Дії']
const HIDDEN_HEADERS = new Set(['Постер', 'Дії'])

function TitlesTable({ query, onPageChange }: { query: UseQueryResult<TitlePage>; onPageChange: (page: number) => void }) {
  if (query.isPending) return <TableSkeleton columns={6} />
  if (query.isError) return <StateMessage tone="error" title="Не вдалося завантажити список" text={errorMessage(query.error)} />
  if (query.data.items.length === 0) {
    return <StateMessage title="Нічого не знайдено" text="Змініть пошуковий запит або додайте новий тайтл" />
  }

  const { items, total, page, page_size } = query.data
  return (
    <div className="space-y-6">
      <div className="overflow-x-auto">
        <table className={`w-full text-left text-sm ${query.isPlaceholderData ? 'opacity-60' : ''}`}>
          <thead className="border-b border-line text-xs text-muted uppercase">
            <tr>
              {HEADERS.map((header) => (
                <th key={header} scope="col" className="py-2 pr-3 font-medium">
                  <span className={HIDDEN_HEADERS.has(header) ? 'sr-only' : undefined}>{header}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {items.map((title) => (
              <AdminTitleRow key={title.id} title={title} />
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} totalPages={Math.ceil(total / page_size)} onChange={onPageChange} />
    </div>
  )
}

export default function AdminTitlesPage() {
  useDocumentTitle('Фільми та серіали — Адмінка')
  const { filters, update } = useCatalogFilters()
  const params: TitleSearchParams = { q: filters.q || undefined, sort: 'name', page: filters.page, page_size: ADMIN_PAGE_SIZE }
  const query = useQuery({
    queryKey: catalogKeys.search(params),
    queryFn: () => catalogApi.search(params),
    placeholderData: keepPreviousData,
  })

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold">Фільми та серіали</h1>
          {query.data && <p className="mt-1 text-sm text-muted">Усього: {query.data.total}</p>}
        </div>
        <Link to="/admin/titles/new" className={buttonPrimary}>
          Додати тайтл
        </Link>
      </div>
      <div className="max-w-sm">
        <SearchInput label="Пошук" placeholder="Назва або опис" value={filters.q} onCommit={(q) => update({ q })} />
      </div>
      <TitlesTable query={query} onPageChange={(page) => update({ page })} />
    </section>
  )
}
