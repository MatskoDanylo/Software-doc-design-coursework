import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { parseReportFilters, reportFiltersToParams, reportParams, type ReportFilters } from './filters'

export function useReportFilters() {
  const [params, setParams] = useSearchParams()
  const [today] = useState(() => new Date())
  const filters = useMemo(() => parseReportFilters(params), [params])
  const query = useMemo(() => reportParams(filters, today), [filters, today])

  const update = useCallback(
    (patch: Partial<ReportFilters>) =>
      setParams((current) => reportFiltersToParams({ ...parseReportFilters(current), ...patch })),
    [setParams],
  )

  return { filters, query, update }
}
