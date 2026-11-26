import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { errorMessage } from '../../../api/errors'
import type { ReportTabId } from '../../../reports/filters'
import { formatFullDate } from '../../../reports/format'
import type { Report } from '../../../types/report'
import PageLoader from '../../PageLoader'
import StateMessage from '../../StateMessage'
import ActivityPanel from './ActivityPanel'
import PopularPanel from './PopularPanel'
import RevenuePanel from './RevenuePanel'
import SummaryTiles from './SummaryTiles'

const PANELS: Record<ReportTabId, (props: { report: Report }) => ReactNode> = {
  popular: PopularPanel,
  activity: ActivityPanel,
  revenue: RevenuePanel,
}

export default function ReportView({ tab, query }: { tab: ReportTabId; query: UseQueryResult<Report> }) {
  if (query.isPending) return <PageLoader />
  if (query.isError) return <StateMessage tone="error" title="Не вдалося побудувати звіт" text={errorMessage(query.error)} />

  const report = query.data
  const Panel = PANELS[tab]
  return (
    <div className={`space-y-8 transition-opacity ${query.isPlaceholderData ? 'opacity-60' : ''}`} aria-busy={query.isFetching}>
      <p className="text-sm text-muted">
        {formatFullDate(report.date_from)} — {formatFullDate(report.date_to)} · часовий пояс {report.timezone}
      </p>
      <SummaryTiles items={report.summary} groupBy={report.group_by} />
      <Panel report={report} />
    </div>
  )
}
