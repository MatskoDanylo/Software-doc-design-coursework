import type { Dashboard, Report, ReportKind, ReportParams } from '../types/report'
import { apiDownload, apiRequest } from './client'

function reportPath(kind: ReportKind, { dateFrom, dateTo, groupBy }: ReportParams, format: 'json' | 'csv'): string {
  const query = new URLSearchParams({ date_from: dateFrom, date_to: dateTo, group_by: groupBy, format })
  return `/api/admin/reports/${kind}?${query}`
}

export const adminReportsApi = {
  report: (kind: ReportKind, params: ReportParams) => apiRequest<Report>(reportPath(kind, params, 'json')),
  csv: (kind: ReportKind, params: ReportParams) => apiDownload(reportPath(kind, params, 'csv')),
  dashboard: () => apiRequest<Dashboard>('/api/admin/dashboard'),
}

export const adminReportKeys = {
  report: (kind: ReportKind, params: ReportParams) => ['admin', 'reports', kind, params] as const,
  dashboard: ['admin', 'dashboard'] as const,
}
