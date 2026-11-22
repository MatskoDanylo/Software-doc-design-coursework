import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { catalogApi, catalogKeys } from '../api/catalog'
import { hasActiveFilters, toSearchParams } from '../catalog/filters'
import { useCatalogFilters } from '../catalog/useCatalogFilters'
import CatalogResults from '../components/catalog/CatalogResults'
import FilterPanel from '../components/catalog/FilterPanel'
import SortSelect from '../components/catalog/SortSelect'

export default function CatalogPage() {
  const { filters, update, reset } = useCatalogFilters()
  const params = toSearchParams(filters)
  const query = useQuery({
    queryKey: catalogKeys.search(params),
    queryFn: () => catalogApi.search(params),
    placeholderData: keepPreviousData,
  })

  const changePage = (page: number) => {
    update({ page })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[17rem_1fr]">
      <FilterPanel filters={filters} onChange={update} onReset={reset} />
      <section aria-labelledby="catalog-heading" className="min-w-0 space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 id="catalog-heading" className="font-display text-3xl font-semibold">
              Каталог
            </h1>
            {query.data && <p className="mt-1 text-sm text-muted">Знайдено: {query.data.total}</p>}
          </div>
          <div className="w-56">
            <SortSelect sort={filters.sort} order={filters.order} onChange={(sort, order) => update({ sort, order })} />
          </div>
        </div>
        <CatalogResults query={query} filtered={hasActiveFilters(filters)} onPageChange={changePage} onReset={reset} />
      </section>
    </div>
  )
}
