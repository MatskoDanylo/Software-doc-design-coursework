import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { errorMessage } from '../api/errors'
import { favoritesApi, favoritesKeys } from '../api/favorites'
import TitleGrid, { TitleGridSkeleton } from '../components/catalog/TitleGrid'
import Pagination from '../components/Pagination'
import StateMessage from '../components/StateMessage'
import { buttonOutline } from '../components/ui'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

function readPage(value: string | null): number {
  const page = Number(value)
  return Number.isInteger(page) && page > 0 ? page : 1
}

function CatalogLink() {
  return (
    <Link to="/catalog" className={buttonOutline}>
      До каталогу
    </Link>
  )
}

export default function FavoritesPage() {
  useDocumentTitle('Вибране')
  const [params, setParams] = useSearchParams()
  const page = readPage(params.get('page'))
  const query = useQuery({
    queryKey: favoritesKeys.page(page),
    queryFn: () => favoritesApi.list(page),
    placeholderData: keepPreviousData,
  })

  const changePage = (next: number) => setParams(next > 1 ? { page: String(next) } : {})

  if (query.data && query.data.items.length === 0 && page > 1 && !query.isPlaceholderData) {
    return <Navigate to={page > 2 ? `?page=${page - 1}` : '/favorites'} replace />
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-display text-3xl font-semibold">Вибране</h1>
        {query.data && query.data.total > 0 && <p className="text-sm text-muted">{query.data.total} тайтл(ів)</p>}
      </div>
      {query.isError ? (
        <StateMessage tone="error" title="Не вдалося завантажити Вибране" text={errorMessage(query.error)} />
      ) : !query.data ? (
        <TitleGridSkeleton />
      ) : query.data.items.length === 0 && page === 1 ? (
        <StateMessage
          title="У Вибраному поки порожньо"
          text="Натисніть на сердечко на картці фільму чи серіалу, щоб зберегти його тут"
          action={<CatalogLink />}
        />
      ) : (
        <>
          <TitleGrid titles={query.data.items} dimmed={query.isPlaceholderData} />
          <Pagination
            page={page}
            totalPages={Math.ceil(query.data.total / query.data.page_size)}
            onChange={changePage}
          />
        </>
      )}
    </section>
  )
}
