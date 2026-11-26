import { useCsvExport } from '../../../reports/queries'
import type { ReportKind, ReportParams } from '../../../types/report'
import { buttonOutline } from '../../ui'

export default function ExportCsvButton({ kind, params }: { kind: ReportKind; params: ReportParams }) {
  const exportCsv = useCsvExport(kind, params)

  return (
    <button type="button" className={buttonOutline} disabled={exportCsv.isPending} onClick={() => exportCsv.mutate()}>
      {exportCsv.isPending ? 'Готуємо файл…' : 'Експорт CSV'}
    </button>
  )
}
