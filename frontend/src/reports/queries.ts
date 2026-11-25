import { useMutation, useQuery } from '@tanstack/react-query'
import { adminReportKeys, adminReportsApi } from '../api/adminReports'
import type { ReportKind, ReportParams } from '../types/report'
import { saveFile } from './download'

export function useReport(kind: ReportKind, params: ReportParams) {
  return useQuery({
    queryKey: adminReportKeys.report(kind, params),
    queryFn: () => adminReportsApi.report(kind, params),
    placeholderData: (previous) => (previous?.kind === kind ? previous : undefined),
  })
}

export function useDashboard() {
  return useQuery({ queryKey: adminReportKeys.dashboard, queryFn: adminReportsApi.dashboard })
}

export function useCsvExport(kind: ReportKind, params: ReportParams) {
  return useMutation({
    mutationFn: () => adminReportsApi.csv(kind, params),
    onSuccess: ({ blob, filename }) => saveFile(blob, filename ?? `${kind}_${params.dateFrom}_${params.dateTo}.csv`),
  })
}
