import { formatCell } from '../../../reports/format'
import type { GroupBy, SummaryItem } from '../../../types/report'
import StatTile from '../StatTile'

export default function SummaryTiles({ items, groupBy }: { items: SummaryItem[]; groupBy: GroupBy }) {
  return (
    <dl aria-label="Підсумки" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {items.map((item) => (
        <StatTile key={item.key} label={item.label} value={formatCell(item.key, item.value, groupBy)} />
      ))}
    </dl>
  )
}
