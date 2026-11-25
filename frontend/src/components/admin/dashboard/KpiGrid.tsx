import { errorMessage } from '../../../api/errors'
import { formatMoney, formatNumber } from '../../../reports/format'
import { useDashboard } from '../../../reports/queries'
import type { Dashboard } from '../../../types/report'
import FormAlert from '../../FormAlert'
import StatTile, { StatTileSkeleton } from '../StatTile'

const KPIS: { key: keyof Dashboard; label: string; format: (value: number) => string }[] = [
  { key: 'total_users', label: 'Користувачів', format: formatNumber },
  { key: 'active_users_7d', label: 'Активних за 7 днів', format: formatNumber },
  { key: 'active_premium', label: 'Активних Premium', format: formatNumber },
  { key: 'revenue_30d', label: 'Дохід за 30 днів', format: formatMoney },
  { key: 'titles_with_video', label: 'Тайтлів з відео', format: formatNumber },
]

export default function KpiGrid() {
  const query = useDashboard()

  if (query.isError) return <FormAlert>Не вдалося завантажити показники: {errorMessage(query.error)}</FormAlert>

  return (
    <dl aria-label="Ключові показники" aria-busy={query.isPending} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {KPIS.map((kpi) =>
        query.data ? (
          <StatTile key={kpi.key} label={kpi.label} value={kpi.format(query.data[kpi.key])} />
        ) : (
          <StatTileSkeleton key={kpi.key} />
        ),
      )}
    </dl>
  )
}
