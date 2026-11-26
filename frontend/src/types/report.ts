export type ReportKind = 'popular-titles' | 'user-activity' | 'subscription-revenue'
export type GroupBy = 'day' | 'month'
export type ReportCell = number | string | null
export type ReportRow = Record<string, ReportCell>

export interface ReportColumn {
  key: string
  label: string
}

export interface ReportSection {
  key: string
  title: string
  columns: ReportColumn[]
  rows: ReportRow[]
}

export interface SummaryItem {
  key: string
  label: string
  value: ReportCell
}

export interface Report {
  kind: ReportKind
  title: string
  date_from: string
  date_to: string
  group_by: GroupBy
  timezone: string
  summary: SummaryItem[]
  sections: ReportSection[]
}

export interface ReportParams {
  dateFrom: string
  dateTo: string
  groupBy: GroupBy
}

export interface Dashboard {
  total_users: number
  active_users_7d: number
  active_premium: number
  revenue_30d: number
  titles_with_video: number
}

export interface DownloadedFile {
  blob: Blob
  filename: string | null
}
