import { formatBucket } from '../../../reports/format'
import { chartPoints, findSection } from '../../../reports/sections'
import type { Report } from '../../../types/report'
import TimeLineChart, { type LineSeries } from '../../charts/TimeLineChart'
import SectionView from './SectionView'

export const ACTIVITY_SERIES = [
  { key: 'registrations', name: 'Реєстрації' },
  { key: 'active_users', name: 'Активні користувачі' },
] as const satisfies readonly [LineSeries, LineSeries]

export default function ActivityPanel({ report }: { report: Report }) {
  const activity = findSection(report, 'activity')
  if (!activity) return null
  const keys = ACTIVITY_SERIES.map((series) => series.key)
  const data = chartPoints(activity.rows, 'bucket', keys, (value) => formatBucket(value, report.group_by))

  return (
    <SectionView section={activity} groupBy={report.group_by} chartTitle="Реєстрації та активні користувачі">
      <TimeLineChart data={data} series={ACTIVITY_SERIES} />
    </SectionView>
  )
}
