import type { UseQueryResult } from '@tanstack/react-query'
import { errorMessage } from '../../api/errors'
import type { TitlePage } from '../../types/catalog'
import Pagination from '../Pagination'
import StateMessage from '../StateMessage'
import { buttonOutline } from '../ui'
import TitleGrid, { TitleGridSkeleton } from './TitleGrid'

interface CatalogResultsProps {
  query: UseQueryResult<TitlePage>
  filtered: boolean
  onPageChange: (page: number) => void
  onReset: () => void
}

export default function CatalogResults({ query, filtered, onPageChange, onReset }: CatalogResultsProps) {
  if (query.isPending) return <TitleGridSkeleton />

  if (query.isError) {
    return (
      <StateMessage
        tone="error"
        title="Не вдалося завантажити каталог"
        text={errorMessage(query.error)}
        action={
          <button type="button" className={buttonOutline} onClick={() => query.refetch()}>
            Спробувати ще раз
          </button>
        }
      />
    )
  }

  const { items, total, page, page_size } = query.data
  if (items.length === 0) {
    return (
      <StateMessage
        title="Нічого не знайдено"
        text={filtered ? 'Спробуйте змінити або скинути фільтри' : 'Каталог поки порожній'}
        action={
          filtered && (
            <button type="button" className={buttonOutline} onClick={onReset}>
              Скинути фільтри
            </button>
          )
        }
      />
    )
  }

  return (
    <div className="space-y-10">
      <TitleGrid titles={items} dimmed={query.isPlaceholderData} />
      <Pagination page={page} totalPages={Math.ceil(total / page_size)} onChange={onPageChange} />
    </div>
  )
}
