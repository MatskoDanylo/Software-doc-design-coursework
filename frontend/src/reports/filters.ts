import type { GroupBy, ReportKind, ReportParams } from '../types/report'
import { daysBefore, parseIsoDate, toIsoDate } from './dates'

export const PERIOD_PRESETS = [7, 30, 90] as const
export type PresetDays = (typeof PERIOD_PRESETS)[number]
export const DEFAULT_PRESET: PresetDays = 30

export type Period = { type: 'preset'; days: PresetDays } | { type: 'custom'; from: string; to: string }

export const REPORT_TABS = [
  { id: 'popular', kind: 'popular-titles', label: 'Популярне', grouped: false },
  { id: 'activity', kind: 'user-activity', label: 'Активність', grouped: true },
  { id: 'revenue', kind: 'subscription-revenue', label: 'Доходи', grouped: true },
] as const satisfies readonly { id: string; kind: ReportKind; label: string; grouped: boolean }[]

export type ReportTab = (typeof REPORT_TABS)[number]
export type ReportTabId = ReportTab['id']

export const REPORT_PANEL_ID = 'report-panel'

export function reportTabId(id: ReportTabId): string {
  return `report-tab-${id}`
}

export interface ReportFilters {
  tab: ReportTabId
  period: Period
  groupBy: GroupBy
}

export const DEFAULT_FILTERS: ReportFilters = {
  tab: 'popular',
  period: { type: 'preset', days: DEFAULT_PRESET },
  groupBy: 'day',
}

function parseTab(value: string | null): ReportTabId {
  return REPORT_TABS.find((tab) => tab.id === value)?.id ?? DEFAULT_FILTERS.tab
}

function parsePeriod(params: URLSearchParams): Period {
  const from = parseIsoDate(params.get('from'))
  const to = parseIsoDate(params.get('to'))
  if (from && to && from <= to) return { type: 'custom', from: toIsoDate(from), to: toIsoDate(to) }
  const days = PERIOD_PRESETS.find((preset) => String(preset) === params.get('days'))
  return { type: 'preset', days: days ?? DEFAULT_PRESET }
}

export function parseReportFilters(params: URLSearchParams): ReportFilters {
  return {
    tab: parseTab(params.get('tab')),
    period: parsePeriod(params),
    groupBy: params.get('group') === 'month' ? 'month' : 'day',
  }
}

export function reportFiltersToParams({ tab, period, groupBy }: ReportFilters): URLSearchParams {
  const params = new URLSearchParams()
  if (tab !== DEFAULT_FILTERS.tab) params.set('tab', tab)
  if (period.type === 'custom') {
    params.set('from', period.from)
    params.set('to', period.to)
  } else if (period.days !== DEFAULT_PRESET) {
    params.set('days', String(period.days))
  }
  if (groupBy !== DEFAULT_FILTERS.groupBy) params.set('group', groupBy)
  return params
}

export function periodRange(period: Period, today: Date): { dateFrom: string; dateTo: string } {
  if (period.type === 'custom') return { dateFrom: period.from, dateTo: period.to }
  return { dateFrom: toIsoDate(daysBefore(today, period.days - 1)), dateTo: toIsoDate(today) }
}

export function reportParams(filters: ReportFilters, today: Date): ReportParams {
  return { ...periodRange(filters.period, today), groupBy: filters.groupBy }
}

export function tabById(id: ReportTabId): ReportTab {
  return REPORT_TABS.find((tab) => tab.id === id) ?? REPORT_TABS[0]
}
