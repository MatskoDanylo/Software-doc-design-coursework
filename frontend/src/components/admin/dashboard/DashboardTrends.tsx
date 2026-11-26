import { useState } from 'react'
import { daysBefore, toIsoDate } from '../../../reports/dates'
import { formatBucket, formatMoney } from '../../../reports/format'
import { useReport } from '../../../reports/queries'
import { chartPoints, findSection } from '../../../reports/sections'
import type { Report, ReportParams } from '../../../types/report'
import TimeBarChart from '../../charts/TimeBarChart'
import TimeLineChart from '../../charts/TimeLineChart'
import TrendCard from './TrendCard'

const TREND_DAYS = 30
const HEIGHT = 180

function trendParams(): ReportParams {
  const today = new Date()
  return { dateFrom: toIsoDate(daysBefore(today, TREND_DAYS - 1)), dateTo: toIsoDate(today), groupBy: 'day' }
}

function points(report: Report | undefined, section: string, key: string) {
  const rows = report ? (findSection(report, section)?.rows ?? []) : []
  return chartPoints(rows, 'bucket', [key], (value) => formatBucket(value, 'day'))
}

export default function DashboardTrends() {
  const [params] = useState(trendParams)
  const activity = useReport('user-activity', params)
  const revenue = useReport('subscription-revenue', params)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <TrendCard title="Активні користувачі за 30 днів" to="/admin/reports?tab=activity" state={activity}>
        <TimeLineChart
          data={points(activity.data, 'activity', 'active_users')}
          series={[{ key: 'active_users', name: 'Активні користувачі' }]}
          height={HEIGHT}
        />
      </TrendCard>
      <TrendCard title="Дохід за 30 днів" to="/admin/reports?tab=revenue" state={revenue}>
        <TimeBarChart
          data={points(revenue.data, 'revenue', 'revenue')}
          dataKey="revenue"
          name="Дохід"
          format={formatMoney}
          height={HEIGHT}
        />
      </TrendCard>
    </div>
  )
}
