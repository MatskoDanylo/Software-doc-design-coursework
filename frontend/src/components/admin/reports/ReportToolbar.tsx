import type { Period, ReportTab } from '../../../reports/filters'
import type { GroupBy, ReportParams } from '../../../types/report'
import SelectField from '../../SelectField'
import ExportCsvButton from './ExportCsvButton'
import PeriodFilter from './PeriodFilter'

const GROUP_OPTIONS = [
  { value: 'day', label: 'По днях' },
  { value: 'month', label: 'По місяцях' },
] as const

interface ReportToolbarProps {
  tab: ReportTab
  period: Period
  params: ReportParams
  onPeriodChange: (period: Period) => void
  onGroupByChange: (groupBy: GroupBy) => void
}

export default function ReportToolbar({ tab, period, params, onPeriodChange, onGroupByChange }: ReportToolbarProps) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-line bg-surface p-4">
      <PeriodFilter period={period} range={params} onChange={onPeriodChange} />
      <div className="flex flex-wrap items-end gap-3">
        {tab.grouped && (
          <div className="w-40">
            <SelectField
              label="Групування"
              options={GROUP_OPTIONS}
              value={params.groupBy}
              onChange={(event) => onGroupByChange(event.target.value === 'month' ? 'month' : 'day')}
            />
          </div>
        )}
        <ExportCsvButton kind={tab.kind} params={params} />
      </div>
    </div>
  )
}
