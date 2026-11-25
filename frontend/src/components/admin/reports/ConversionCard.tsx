import { formatNumber } from '../../../reports/format'
import { numeric } from '../../../reports/sections'
import type { Report } from '../../../types/report'
import { SERIES_COLORS } from '../../charts/theme'

function summaryValue(report: Report, key: string): number {
  return numeric(report.summary.find((item) => item.key === key)?.value)
}

export default function ConversionCard({ report }: { report: Report }) {
  const conversion = summaryValue(report, 'conversion')
  const payers = summaryValue(report, 'paying_users')

  return (
    <section aria-label="Конверсія" className="rounded-2xl border border-line bg-surface p-5">
      <h2 className="text-sm font-medium text-zinc-200">Конверсія free → premium</h2>
      <p className="mt-3 font-display text-4xl font-semibold tabular-nums">{formatNumber(conversion)}%</p>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-raised" aria-hidden="true">
        <div className="h-full rounded-full" style={{ width: `${Math.min(conversion, 100)}%`, background: SERIES_COLORS[0] }} />
      </div>
      <p className="mt-3 text-sm text-muted">
        Оплатили за період: {formatNumber(payers)}. Частка від усіх користувачів, зареєстрованих на кінець періоду.
      </p>
    </section>
  )
}
