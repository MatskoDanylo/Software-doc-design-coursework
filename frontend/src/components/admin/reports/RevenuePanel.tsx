import { formatBucket, formatMoney, statusLabel } from '../../../reports/format'
import { chartPoints, findSection } from '../../../reports/sections'
import type { Report } from '../../../types/report'
import RankedBarChart from '../../charts/RankedBarChart'
import TimeBarChart from '../../charts/TimeBarChart'
import ConversionCard from './ConversionCard'
import SectionView from './SectionView'

export default function RevenuePanel({ report }: { report: Report }) {
  const revenue = findSection(report, 'revenue')
  const statuses = findSection(report, 'statuses')
  const bucketLabel = (value: string) => formatBucket(value, report.group_by)

  return (
    <div className="space-y-10">
      {revenue && (
        <SectionView section={revenue} groupBy={report.group_by} chartTitle="Дохід, грн">
          <TimeBarChart
            data={chartPoints(revenue.rows, 'bucket', ['revenue'], bucketLabel)}
            dataKey="revenue"
            name="Дохід"
            format={formatMoney}
          />
        </SectionView>
      )}
      <div className="grid items-start gap-6 lg:grid-cols-[2fr_1fr]">
        {statuses && (
          <SectionView section={statuses} groupBy={report.group_by} chartTitle="Кількість платежів за статусом">
            <RankedBarChart data={chartPoints(statuses.rows, 'status', ['count'], statusLabel)} dataKey="count" name="Платежів" />
          </SectionView>
        )}
        <ConversionCard report={report} />
      </div>
    </div>
  )
}
