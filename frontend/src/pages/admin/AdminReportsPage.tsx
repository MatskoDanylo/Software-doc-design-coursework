import ReportTabs from '../../components/admin/reports/ReportTabs'
import ReportToolbar from '../../components/admin/reports/ReportToolbar'
import ReportView from '../../components/admin/reports/ReportView'
import { REPORT_PANEL_ID, reportTabId, tabById } from '../../reports/filters'
import { useReport } from '../../reports/queries'
import { useReportFilters } from '../../reports/useReportFilters'

export default function AdminReportsPage() {
  const { filters, query, update } = useReportFilters()
  const tab = tabById(filters.tab)
  const report = useReport(tab.kind, query)

  return (
    <section className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Звіти</h1>
        <p className="mt-1 text-sm text-muted">Період і групування зберігаються в адресі сторінки, тож посиланням можна поділитися.</p>
      </div>
      <ReportTabs active={tab.id} onSelect={(id) => update({ tab: id })} />
      <div role="tabpanel" id={REPORT_PANEL_ID} aria-labelledby={reportTabId(tab.id)} className="space-y-6">
        <ReportToolbar
          tab={tab}
          period={filters.period}
          params={query}
          onPeriodChange={(period) => update({ period })}
          onGroupByChange={(groupBy) => update({ groupBy })}
        />
        <ReportView tab={tab.id} query={report} />
      </div>
    </section>
  )
}
