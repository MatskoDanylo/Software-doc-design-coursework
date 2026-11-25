import { formatCell } from '../../../reports/format'
import type { GroupBy, ReportSection } from '../../../types/report'

const cellClass = (value: unknown) => `py-2 pr-4 ${typeof value === 'number' ? 'text-right tabular-nums' : ''}`

export default function ReportTable({ section, groupBy }: { section: ReportSection; groupBy: GroupBy }) {
  const { columns, rows } = section

  return (
    <div className="max-h-96 overflow-auto rounded-xl border border-line">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">{section.title}</caption>
        <thead className="sticky top-0 bg-surface text-xs text-muted">
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className="py-2 pr-4 font-medium first:pl-4">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-6 text-center text-muted">
                За цей період даних немає
              </td>
            </tr>
          )}
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key} className={`${cellClass(row[column.key])} first:pl-4`}>
                  {formatCell(column.key, row[column.key] ?? null, groupBy)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
