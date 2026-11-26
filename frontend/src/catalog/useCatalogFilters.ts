import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { DEFAULT_FILTERS, filtersToParams, parseFilters, type CatalogFilters } from './filters'

export function useCatalogFilters() {
  const [params, setParams] = useSearchParams()
  const filters = useMemo(() => parseFilters(params), [params])

  const update = useCallback(
    (patch: Partial<CatalogFilters>) => {
      setParams((current) => filtersToParams({ ...parseFilters(current), page: 1, ...patch }))
    },
    [setParams],
  )

  const reset = useCallback(() => {
    setParams((current) => {
      const { sort, order } = parseFilters(current)
      return filtersToParams({ ...DEFAULT_FILTERS, sort, order })
    })
  }, [setParams])

  return { filters, update, reset }
}
