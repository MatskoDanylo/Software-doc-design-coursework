import type { Report, ReportCell, ReportRow, ReportSection } from '../types/report'

export interface ChartPoint {
  label: string
  [series: string]: string | number
}

export function findSection(report: Report, key: string): ReportSection | undefined {
  return report.sections.find((section) => section.key === key)
}

export function numeric(value: ReportCell | undefined): number {
  return typeof value === 'number' ? value : 0
}

export function chartPoints(
  rows: readonly ReportRow[],
  labelKey: string,
  seriesKeys: readonly string[],
  formatLabel: (value: string) => string = (value) => value,
): ChartPoint[] {
  return rows.map((row) => {
    const point: ChartPoint = { label: formatLabel(String(row[labelKey] ?? '')) }
    for (const key of seriesKeys) point[key] = numeric(row[key])
    return point
  })
}
